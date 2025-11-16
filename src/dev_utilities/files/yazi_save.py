import typer
from typing_extensions import Annotated

from .yazi_load import update_file, yazi_data_prefix, list_files_with_prefix

def main(
    name: Annotated[str, typer.Argument()] = None
):
    if name:
        update_file( "~/.local/state/yazi/.dds", f"~/.local/state/yazi/{yazi_data_prefix}{name}")
    else:
        for file in list_files_with_prefix("~/.local/state/yazi/", yazi_data_prefix):
            print(file.name[len(yazi_data_prefix):])


if __name__ == "__main__":
    typer.run(main)
