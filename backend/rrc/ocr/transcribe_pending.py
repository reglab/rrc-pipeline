import click
import tqdm
from sqlalchemy import select
from sqlalchemy.orm import Session

from rrc.db.models import Page, Provenance, Transcription
from rrc.db.session import get_session
from rrc.ocr.service import DoctrOCRService
from rrc.utils.logger import LOGGER
from rrc.utils.types import OCRResult

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
        LOGGER.info("No pending pages found")
        return

    LOGGER.info("Found %d pages pending transcription", pending_count)

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

    LOGGER.info("Completed processing all pending pages")


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
