from pathlib import Path

import click
import tqdm
from rich.console import Console
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

import rrc.utils.io
from rrc.db.models import CovenantPrediction, Page, Provenance
from rrc.db.session import get_session
from rrc.inference.service import (
    InferenceService,
    MistralInferenceService,
    QwenInferenceService,
)
from rrc.utils.types import InferenceResult

console = Console()

_DEFAULT_BATCH_SIZE = 250
_DEFAULT_MODEL_NAME_OR_PATH = "reglab-rrc/qwen-rrc"
_DEFAULT_MODEL_DOWNLOAD_DIR = rrc.utils.io.get_data_path("model_cache")
_DEFAULT_MODEL_TYPE = "qwen"


_MODEL_TYPE_CLASS_MAP: dict[str, type[InferenceService]] = {
    "mistral": MistralInferenceService,
    "qwen": QwenInferenceService,
}


def _get_pending_count(session: Session) -> int:
    stmt = (
        select(func.count())
        .select_from(Page)
        .where(Page.transcriptions.any(), ~Page.predictions.any())
    )
    return session.scalar(stmt) or 0


def _get_next_batch(session: Session, batch_size: int, last_id: int) -> list[Page]:
    stmt = (
        select(Page)
        .options(joinedload(Page.transcriptions))
        .where(Page.transcriptions.any(), ~Page.predictions.any(), Page.id > last_id)
        .order_by(Page.id)
        .limit(batch_size)
    )
    return list(session.execute(stmt).unique().scalars().all())


def _save_predictions(
    session: Session,
    pages: list[Page],
    results: list[InferenceResult | None],
    provenance: Provenance,
) -> None:
    for page, result in zip(pages, results, strict=True):
        if result is None:
            console.print(
                f"[yellow]⚠[/yellow] Failed to get prediction for page [cyan]{page.id}[/cyan]"
            )
            continue

        prediction = CovenantPrediction(
            page=page,
            transcription=page.transcriptions[0],
            provenance=provenance,
            answer=result.answer,
            confidence=result.confidence,
            raw_passage=result.raw_passage,
            quotation=result.quotation,
        )
        session.add(prediction)

    session.commit()


@click.command()
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=_DEFAULT_BATCH_SIZE,
    show_default=True,
    help="Number of pages to process in each batch",
)
@click.option(
    "--model-name-or-path",
    "-m",
    type=str,
    default=_DEFAULT_MODEL_NAME_OR_PATH,
    show_default=True,
    help="Name or path of the model to use",
)
@click.option(
    "--model-download-dir",
    "-d",
    type=click.Path(path_type=Path),
    default=_DEFAULT_MODEL_DOWNLOAD_DIR,
    show_default=True,
)
@click.option(
    "--model-type",
    "-t",
    type=click.Choice(["mistral", "qwen"]),
    default=_DEFAULT_MODEL_TYPE,
    show_default=True,
)
def main(
    batch_size: int, model_name_or_path: str, model_download_dir: Path, model_type: str
) -> None:
    """Process all pages with transcriptions but no predictions."""
    session = get_session()
    last_id = 0
    pending_count = _get_pending_count(session)
    if pending_count == 0:
        console.print(
            "[yellow]⚠[/yellow] No pending pages found - all pages already have predictions"
        )
        return

    console.print(
        f"[green]🔍[/green] Found [bold blue]{pending_count}[/bold blue] pages pending prediction"
    )
    console.print(
        f"[green]🤖[/green] Using model: [cyan]{model_name_or_path}[/cyan] (type: [magenta]{model_type}[/magenta], batch size: [cyan]{batch_size}[/cyan])"
    )

    with _MODEL_TYPE_CLASS_MAP[model_type](
        {
            "model_name_or_path": model_name_or_path,
            "model_download_dir": model_download_dir,
        }
    ) as service:
        provenance = service.get_provenance()
        provenance.creator = "detect_pending"
        pbar = tqdm.tqdm(total=pending_count, desc="Processing pages")
        while True:
            batch = _get_next_batch(session, batch_size, last_id)
            if not batch:
                break

            results = service.predict([page.as_text_input() for page in batch])
            _save_predictions(session, batch, results, provenance)
            last_id = batch[-1].id
            pbar.update(len(batch))

    console.print(
        f"[green]✓[/green] Successfully completed processing [bold blue]{pending_count}[/bold blue] pages with predictions"
    )


if __name__ == "__main__":
    main()
