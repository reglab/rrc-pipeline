import csv
from datetime import datetime
from pathlib import Path

import click
import tqdm
from rich.console import Console
from sqlalchemy import select
from sqlalchemy.orm import joinedload

import rrc.utils.io
from rrc.db.models import CovenantPrediction
from rrc.db.session import get_session

console = Console()

_DEFAULT_OUTPUT_DIR = rrc.utils.io.get_data_path(
    "reports", datetime.now().strftime("%Y%m%d_%H%M%S")
)
_CSV_FIELDS = [
    "image_path",
    "frame_idx",
    "positive_prob",
    "raw_passage",
    "quotation",
    "model_name",
    "prediction_id",
    "created_at",
]


@click.command()
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(path_type=Path),
    default=_DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Directory to write CSV files to",
)
def main(output_dir: Path) -> None:
    """Export covenant predictions to CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    session = get_session()

    stmt = select(CovenantPrediction).options(joinedload(CovenantPrediction.page))
    predictions: list[CovenantPrediction] = session.execute(stmt).scalars().all()
    console.print(
        f"[green]📊[/green] Found [bold blue]{len(predictions)}[/bold blue] predictions to export to [cyan]{output_dir}[/cyan]"
    )

    pos_count = neg_count = 0
    with (
        (output_dir / "positive.csv").open("w") as pos_f,
        (output_dir / "negative.csv").open("w") as neg_f,
    ):
        pos_writer = csv.DictWriter(pos_f, fieldnames=_CSV_FIELDS)
        neg_writer = csv.DictWriter(neg_f, fieldnames=_CSV_FIELDS)
        pos_writer.writeheader()
        neg_writer.writeheader()

        for pred in tqdm.tqdm(predictions, desc="Exporting predictions"):
            row = {
                "image_path": pred.page.image_path,
                "frame_idx": pred.page.image_frame_idx,
                "positive_prob": pred.confidence,
                "raw_passage": pred.raw_passage,
                "quotation": pred.quotation,
                "model_name": pred.provenance.model_name,
                "prediction_id": pred.id,
                "created_at": pred.created_at.isoformat(),
            }
            if pred.answer:
                pos_writer.writerow(row)
                pos_count += 1
            else:
                neg_writer.writerow(row)
                neg_count += 1

    console.print(
        f"[green]✓[/green] Successfully exported [bold green]{pos_count}[/bold green] positive and "
        f"[bold red]{neg_count}[/bold red] negative predictions to [cyan]{output_dir}[/cyan]"
    )


if __name__ == "__main__":
    main()
