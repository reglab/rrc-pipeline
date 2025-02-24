import click
from rich.console import Console
from rich.progress_bar import ProgressBar
from rich.table import Table
from sqlalchemy import func, select

from rrc.db.models import CovenantPrediction, Page, Transcription
from rrc.db.session import get_session

console = Console()


def create_image_stats_table(session) -> Table:
    """Create table showing image/page statistics."""
    table = Table(title="Image Statistics", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")

    total_pages = session.scalar(select(func.count(Page.id)))
    unique_images = session.scalar(select(func.count(func.distinct(Page.image_path))))
    multiframe_count = session.scalar(
        select(func.count(func.distinct(Page.image_path))).where(
            Page.image_frame_idx.is_not(None)
        )
    )

    table.add_row("Total Pages", f"{total_pages:,}")
    table.add_row("Unique Image Files", f"{unique_images:,}")
    table.add_row("Multi-frame Images", f"{multiframe_count:,}")
    return table


def create_processing_stats_table(session) -> Table:
    """Create table showing processing progress with visual bars."""
    table = Table(title="Processing Progress", header_style="bold")
    table.add_column("Stage")
    table.add_column("Progress")
    table.add_column("Status", width=40)

    total_pages = session.scalar(select(func.count(Page.id)))
    ocr_count = session.scalar(select(func.count(func.distinct(Transcription.page_id))))
    pred_count = session.scalar(
        select(func.count(func.distinct(CovenantPrediction.page_id)))
    )

    ocr_pct = ocr_count / total_pages if total_pages else 0
    pred_pct = pred_count / total_pages if total_pages else 0

    table.add_row(
        "OCR",
        f"{ocr_count:,}/{total_pages:,} ({ocr_pct:.1%})",
        ProgressBar(total=100, completed=int(ocr_pct * 100), width=35),
    )
    table.add_row(
        "Detection",
        f"{pred_count:,}/{total_pages:,} ({pred_pct:.1%})",
        ProgressBar(total=100, completed=int(pred_pct * 100), width=35),
    )
    return table


@click.command()
def main() -> None:
    """Display a summary of the current database state."""
    session = get_session()

    console.print(create_image_stats_table(session))
    console.print()
    console.print(create_processing_stats_table(session))


if __name__ == "__main__":
    main()
