import typer
from typing_extensions import Annotated

from pathlib import Path

yazi_data_prefix = "dds_"

import shutil
from pathlib import Path

def update_file(source: str | Path, destination: str | Path) -> Path:
    src = Path(source).expanduser()
    dst = Path(destination).expanduser()
    if dst.exists():
        dst.unlink()
    return Path(shutil.copy(str(src), str(dst)))


def list_files_with_prefix(directory: str, prefix: str) -> list[Path]:
    dir_path = Path(directory).expanduser()
    return [file for file in dir_path.glob(f"{prefix}*") if file.is_file()]

def main(
    name: Annotated[str, typer.Argument()] = None
):
    if name:
        update_file(f"~/.local/state/yazi/{yazi_data_prefix}{name}", "~/.local/state/yazi/.dds")
    else:
        for file in list_files_with_prefix("~/.local/state/yazi/", yazi_data_prefix):
            print(file.name[len(yazi_data_prefix):])


if __name__ == "__main__":
    typer.run(main)
