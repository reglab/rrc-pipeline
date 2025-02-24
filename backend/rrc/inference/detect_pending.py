import click
import tqdm
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

import rrc.utils.io
from rrc.db.models import CovenantPrediction, Page, Provenance
from rrc.db.session import get_session
from rrc.inference.service import MistralInferenceService
from rrc.utils.logger import LOGGER
from rrc.utils.types import InferenceResult

_DEFAULT_BATCH_SIZE = 250
_DEFAULT_MODEL_NAME_OR_PATH = "reglab-rrc/mistral-rrc"
_DEFAULT_MODEL_DOWNLOAD_DIR = rrc.utils.io.get_data_path("model_cache")


def _get_pending_count(session: Session) -> int:
    stmt = select(Page).where(Page.transcriptions.any(), ~Page.predictions.any())
    return len(session.scalars(stmt).all())


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
            LOGGER.warning("Failed to get prediction for page %d", page.id)
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
    type=str,
    default=_DEFAULT_MODEL_DOWNLOAD_DIR,
    show_default=True,
)
def main(batch_size: int, model_name_or_path: str, model_download_dir: str) -> None:
    """Process all pages with transcriptions but no predictions."""
    session = get_session()
    last_id = 0
    pending_count = _get_pending_count(session)
    if pending_count == 0:
        LOGGER.info("No pending pages found")
        return

    LOGGER.info("Found %d pages pending prediction", pending_count)

    with MistralInferenceService(
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

    LOGGER.info("Completed processing all pending pages")


if __name__ == "__main__":
    main()
