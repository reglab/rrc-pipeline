#!/usr/bin/env python
import sys
from pathlib import Path


def add_ts_nocheck(file_path: Path):
    with file_path.open("r+") as f:
        content = f.read()
        if not content.lstrip().startswith("// @ts-nocheck"):
            f.seek(0, 0)
            f.write("// @ts-nocheck\n" + content)


if __name__ == "__main__":
    for file_path in sys.argv[1:]:
        if Path(file_path).suffix in (".ts", ".tsx"):
            add_ts_nocheck(Path(file_path))
