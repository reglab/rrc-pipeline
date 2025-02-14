import csv
import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import dotenv
import requests
import tqdm
from pydantic import BaseModel

DOTENV_LOADED = False


def ensure_dotenv_loaded():
    global DOTENV_LOADED
    if not DOTENV_LOADED:
        dotenv.load_dotenv()
        DOTENV_LOADED = True


def get_data_path(*args) -> Path:
    """Get the path to a file nested in the data directory. If the DATA_ROOT environment
    variable is set, use that as the root directory. Otherwise, use the data directory
    in the project root.

    Args:
        *args: The path components (strings or Path objects) to append to the data root.
    """
    if data_root := getenv("RRC_DATA_ROOT"):
        return Path(data_root).joinpath(*args)
    raise ValueError("RRC_DATA_ROOT environment variable is not set.")


def getenv(name: str, default=None) -> str:
    """Get an environment variable. If the variable is not set, return the default value.

    Ensures that the .env file is loaded before attempting to get the environment variable.

    Args:
        name: The name of the environment variable.
        default: The default value to return if the environment variable is not set.
    """
    ensure_dotenv_loaded()
    return os.getenv(name, default)


def read_jsonl(
    filename: str | Path, *, pydantic_cls: type[BaseModel] | None = None
) -> Iterable[Any]:
    filename = Path(filename)
    with filename.open() as f:
        for line in f:
            if pydantic_cls:
                yield pydantic_cls.model_validate_json(line)
            else:
                yield json.loads(line)


def write_jsonl(
    filename: str | Path, records: Iterable[Any], *, overwrite=False
) -> None:
    filename = Path(filename)
    if filename.exists() and not overwrite:
        raise ValueError(f"{filename} already exists and overwrite is not set.")
    with filename.open("w") as f:
        for record in records:
            json_record: str
            if isinstance(record, BaseModel):
                json_record = record.model_dump_json()
            else:
                json_record = json.dumps(record)
            f.write(json_record + "\n")


def read_csv(
    filename: str | Path, *, pydantic_cls: type[BaseModel] | None = None
) -> Iterable[dict[str, Any]]:
    filename = Path(filename)
    with filename.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            if pydantic_cls:
                yield pydantic_cls.model_validate(row)
            else:
                yield row


def write_csv(
    filename: str | Path,
    records: Iterable[dict[str, Any]],
    *,
    field_names: list[str] | None = None,
    overwrite=False,
) -> None:
    filename = Path(filename)
    if filename.exists() and not overwrite:
        raise ValueError(f"{filename} already exists and overwrite is not set.")
    kwargs = (
        {
            "fieldnames": field_names,
        }
        if field_names
        else {}
    )
    with filename.open("w") as f:
        writer = csv.DictWriter(f, **kwargs)  # type: ignore
        writer.writeheader()
        writer.writerows(records)


def download(url: str, dest: str | Path) -> None:
    """Download a file from a URL to a destination path, with a progress bar.

    Args:
        url: The URL to download from.
        dest: The destination path.
    """
    dest = Path(dest)
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    with (
        dest.open("wb") as f,
        tqdm.tqdm(
            desc=str(dest),
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar,
    ):
        for data in response.iter_content(chunk_size=1024):
            f.write(data)
            pbar.update(len(data))
