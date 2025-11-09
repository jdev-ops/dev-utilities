from typing import Annotated

import typer
from tomlkit import (
    dumps,
    parse,  # you can also use loads
)


def deep_merge_concat(d1, d2):
    for k, v in d2.items():
        if k in d1:
            if isinstance(d1[k], dict) and isinstance(v, dict):
                deep_merge_concat(d1[k], v)
            elif isinstance(d1[k], list) and isinstance(v, list):
                d1[k] += v
            elif isinstance(d1[k], str) and isinstance(v, str):
                d1[k] += v
            else:
                d1[k] = v
        else:
            d1[k] = v


def deep_merge_replace(d1, d2):
    for k, v in d2.items():
        if k in d1:
            if isinstance(d1[k], dict) and isinstance(v, dict):
                deep_merge_replace(d1[k], v)
            else:
                d1[k] = v
        else:
            d1[k] = v


def main(
    in1: Annotated[str, typer.Argument()],
    in2: Annotated[str, typer.Argument()],
    out: Annotated[str, typer.Argument()],
):
    with open(f"{in1}.toml", "r") as f1, open(f"{in2}.toml", "r") as f2:
        data1 = parse(f1.read())
        data2 = parse(f2.read())

    deep_merge_concat(data1, data2)

    with open(f"{out}.toml", "w") as f_out:
        f_out.write(dumps(data1))


def update(
    in1: Annotated[str, typer.Argument()],
    in2: Annotated[str, typer.Argument()],
    out: Annotated[str, typer.Argument()],
):
    with open(f"{in1}.toml", "r") as f1, open(f"{in2}.toml", "r") as f2:
        data1 = parse(f1.read())
        data2 = parse(f2.read())

    deep_merge_replace(data1, data2)

    with open(f"{out}.toml", "w") as f_out:
        f_out.write(dumps(data1))
