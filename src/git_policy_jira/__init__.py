from attrs import define, field
import cattrs
import attrs


@define
class Sprint:
    id: int = field()
    state: str = field()


@define
class Sprints:
    values: list[Sprint] = field()


@define
class Status:
    name: str = field()


@define
class Assignee:
    emailAddress: str | None = field(
                                default=None,
                                validator=attrs.validators.optional(
                                    attrs.validators.instance_of(str)
                                ))


@define
class Field:
    status: Status = field()
    summary: str = field()
    assignee: Assignee | None = field()


@define
class Issue:
    id: str = field()
    key: str = field()
    fields: Field = field()


@define
class Issues:
    issues: list[Issue] = field()
