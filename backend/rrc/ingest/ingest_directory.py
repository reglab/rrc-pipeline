from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import TypeVar

import PIL.Image
import tqdm
from rich.console import Console
from sqlalchemy import select

import rrc.utils.click as click
from rrc.db.models import Page
from rrc.db.session import get_session
from rrc.utils.io import get_image_path

console = Console()

_VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}
_MIN_FILE_SIZE = 1024  # Below 1 KB is probably not a real image, we'll save our effort

_DEFAULT_IMAGE_DIR = get_image_path()


def _get_image_paths(directory: Path) -> list[Path]:
    """Get all image files in directory recursively."""
    image_paths: list[Path] = []
    for ext in _VALID_EXTENSIONS:
        image_paths.extend(directory.rglob(f"*{ext}"))
    return sorted(
        [
            p
            for p in image_paths
            if p.stat().st_size >= _MIN_FILE_SIZE and not p.name.startswith(".")
        ]
    )


def _validate_and_get_frame_count(path: Path) -> int | None:
    """Validate image can be opened and return number of frames if multi-frame."""
    try:
        with PIL.Image.open(path) as img:
            n_frames = getattr(img, "n_frames", 1)
            return n_frames
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to open image [cyan]{path}[/cyan]: {e}")
        return None


def _get_existing_paths(session) -> defaultdict[str, set[int | None]]:
    """Get mapping of image paths to their existing frame indices."""
    stmt = select(Page.image_path, Page.image_frame_idx)
    existing = defaultdict(set)
    for path, frame_idx in session.execute(stmt):
        existing[path].add(frame_idx)
    return existing


def _create_page_records(session, paths: list[Path]) -> None:
    """Create Page records for new image paths."""
    pbar = tqdm.tqdm(total=len(paths), desc="Validating/ingesting images")
    success = fail = 0

    for batch in _chunks(paths, 1000):
        pages = []
        for path in batch:
            n_frames = _validate_and_get_frame_count(path)
            if n_frames is None:
                fail += 1
                pbar.set_postfix(success=success, failed=fail)
                continue

            if n_frames == 1:
                pages.append(Page(image_path=str(path.resolve()), image_frame_idx=None))
            else:
                pages.extend(
                    Page(image_path=str(path.resolve()), image_frame_idx=i)
                    for i in range(n_frames)
                )
            success += 1
            pbar.set_postfix(success=success, failed=fail)

        if pages:
            session.add_all(pages)
            session.commit()
        pbar.update(len(batch))


T = TypeVar("T")


def _chunks(lst: list[T], n: int) -> Iterator[list[T]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


@click.command()
@click.option(
    "-i",
    "--input-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=_DEFAULT_IMAGE_DIR,
    show_default=True,
    help="Directory containing images to ingest",
)
def main(input_dir: Path) -> None:
    """Create Page records for all images in a directory that don't already exist."""
    session = get_session()

    image_paths = _get_image_paths(input_dir)
    if not image_paths:
        console.print(
            f"[yellow]⚠[/yellow] No image files found in [cyan]{input_dir}[/cyan]"
        )
        return

    console.print(
        f"[green]✓[/green] Found [bold blue]{len(image_paths)}[/bold blue] image files in [cyan]{input_dir}[/cyan]"
    )

    existing_paths = _get_existing_paths(session)
    console.print(
        f"[green]✓[/green] Found [bold blue]{len(existing_paths)}[/bold blue] existing page records in database"
    )

    new_paths = [p for p in image_paths if str(p.resolve()) not in existing_paths]
    if not new_paths:
        console.print(
            "[yellow]⚠[/yellow] No new images to ingest - all images already processed"
        )
        return

    console.print(
        f"[green]➤[/green] Ingesting [bold blue]{len(new_paths)}[/bold blue] new images..."
    )
    _create_page_records(session, new_paths)
    console.print(
        f"[green]✓[/green] Successfully completed ingesting [bold blue]{len(new_paths)}[/bold blue] new images"
    )


if __name__ == "__main__":
    main()
