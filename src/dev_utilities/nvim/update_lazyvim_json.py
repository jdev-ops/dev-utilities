import json
import os

from more_itertools import flatten


def is_active(var: str) -> bool:
    res = os.environ.get(var)
    return res == "true" if res else False


def run():
    prefix = "lazyvim.plugins.extras."
    variables = {
        "MASON_PYTHON_EXTRA_ACTIVE": ["formatting.black", "lang.python"],
        "MASON_FRONTEND_ACTIVE": ["formatting.prettier"],
        "MASON_MARKDOWN_ACTIVE": ["lang.markdown"],
        "METALS_SERVER_ACTIVE": ["lang.scala"],
        "NULL_LS_SQL_ACTIVE": ["lang.sql"],
    }

    confs_path = f"{os.environ.get('HOME')}/.config/nvim/lazyvim.json"

    vls = open(confs_path, "r")
    content = json.loads(vls.read())

    entries = [x for x in variables.values()]
    entries = flatten(entries)
    entries = [f"{prefix}{x}" for x in entries]
    entries_set = set(entries)
    difference = list(set(content["extras"]) - entries_set)
    res = [[f"{prefix}{x}" for x in v] for k, v in variables.items() if is_active(k)]
    res.append(difference)
    res = list(flatten(res))
    content["extras"] = res
    content = json.dumps(content, indent=2)

    vls = open(confs_path, "w")
    vls.write(content)
