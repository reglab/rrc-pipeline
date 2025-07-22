"""Main CLI for the RRC (Racial Restrictive Covenants) pipeline."""

import rrc.utils.click as click
from rrc.inference.detect_pending import main as detect_cmd
from rrc.ingest.ingest_directory import main as ingest_cmd
from rrc.ocr.transcribe_pending import main as ocr_cmd
from rrc.reporting.export_predictions import main as export_cmd
from rrc.reporting.summarize_db import main as summarize_cmd


@click.group()
@click.version_option()
def cli():
    """
    RRC Pipeline - Racial Restrictive Covenants Detection

    A comprehensive pipeline for identifying racial covenants in property deeds.
    Process images through OCR, detect covenants with ML models, and export results.
    See https://reglab.github.io/racialcovenants/ for more information.
    """
    pass


# Add the original commands to the CLI group with new names and emojis in help
cli.add_command(ingest_cmd, name="ingest")
cli.add_command(ocr_cmd, name="ocr")
cli.add_command(detect_cmd, name="detect")
cli.add_command(export_cmd, name="export")
cli.add_command(summarize_cmd, name="summarize")

# Update the help text for each command to add emojis
ingest_cmd.help = ingest_cmd.help or "Ingest images from a directory into the database"
ocr_cmd.help = ocr_cmd.help or "Transcribe pending pages using OCR"
detect_cmd.help = (
    detect_cmd.help or "Detect covenants in transcribed pages using ML models"
)
export_cmd.help = export_cmd.help or "Export covenant predictions to CSV files"
summarize_cmd.help = (
    summarize_cmd.help or "Display a summary of the current database state"
)


if __name__ == "__main__":
    cli()
