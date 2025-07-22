import tqdm
from rich.console import Console
from sqlalchemy import select
from sqlalchemy.orm import Session

import rrc.utils.click as click
from rrc.db.models import Page, Provenance, Transcription
from rrc.db.session import get_session
from rrc.ocr.service import DoctrOCRService
from rrc.utils.types import OCRResult

console = Console()

_DEFAULT_BATCH_SIZE = 50


@click.command()
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=_DEFAULT_BATCH_SIZE,
    show_default=True,
    help="Number of pages to process in each batch",
)
def main(batch_size: int) -> None:
    """Process all pages without transcriptions."""
    session = get_session()
    last_id = 0

    # Get count of pending pages
    pending_count = _get_pending_count(session)
    if pending_count == 0:
        console.print(
            "[yellow]⚠[/yellow] No pending pages found - all pages already transcribed"
        )
        return

    console.print(
        f"[green]📄[/green] Found [bold blue]{pending_count}[/bold blue] pages pending transcription (batch size: [cyan]{batch_size}[/cyan])"
    )

    # Process in batches
    with DoctrOCRService() as service:
        provenance = service.get_provenance()
        provenance.creator = "transcribe_pending"
        pbar = tqdm.tqdm(total=pending_count, desc="Processing pages")
        while True:
            batch = _get_next_batch(session, batch_size, last_id)
            if not batch:
                break

            results = service.predict([page.as_ocr_input() for page in batch])
            _save_transcriptions(session, batch, results, provenance)
            last_id = batch[-1].id
            pbar.update(len(batch))

    console.print(
        f"[green]✓[/green] Successfully completed transcribing [bold blue]{pending_count}[/bold blue] pages"
    )


def _get_pending_count(session: Session) -> int:
    stmt = select(Page).where(~Page.transcriptions.any())
    return len(session.scalars(stmt).all())


def _get_next_batch(session: Session, batch_size: int, last_id: int) -> list[Page]:
    stmt = (
        select(Page)
        .where(~Page.transcriptions.any(), Page.id > last_id)
        .order_by(Page.id)
        .limit(batch_size)
    )
    return list(session.scalars(stmt))


def _save_transcriptions(
    session: Session,
    pages: list[Page],
    results: list[OCRResult],
    provenance: Provenance,
) -> None:
    for page, result in zip(pages, results, strict=True):
        transcription = Transcription(
            page=page, provenance=provenance, text=result.text
        )
        session.add(transcription)

    session.commit()


if __name__ == "__main__":
    main()
