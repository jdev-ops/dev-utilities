from collections.abc import Iterable
from pathlib import Path

import cattrs
from attrs import define, field


@define
class Box:
    name: str = field()
    image: str = field()
    host: str = field()


@define
class Boxes:
    boxes: list[Box] = field()


@define
class Machine:
    port: int = field()
    image: str = field()
    host: str = field()


converter = cattrs.Converter()
