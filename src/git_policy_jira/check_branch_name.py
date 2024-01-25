#!/usr/bin/env python

import sys
import re
import os
from git import Repo
from pathlib import Path
from decouple import config as decouple_config
from decouple import Config, RepositoryEnv

if os.environ.get("CONFIG_PATH"):
    config = Config(RepositoryEnv(os.environ["CONFIG_PATH"]))
elif Path(".env.local").is_file():
    config = Config(RepositoryEnv(".env.local"))
else:
    config = decouple_config

def main():
    TASKS_TYPES = config(
        "TASKS_TYPES",
        default="feat|fix|bugfix|config|refactor|build|ci|docs|test",
    )
    VERIFIER_TASKS_KEYS = config("TASKS_KEYS", default="ZDLY-[0-9]+")

    repo = Repo(".")

    types = TASKS_TYPES
    task_management_key = VERIFIER_TASKS_KEYS
    description = "[A-Za-z0-9\\-]+"

    pattern = f"^({types})/{task_management_key}{description}$"

    if not re.search(pattern, str(repo.active_branch)):
        print(
            f"Active branch name is not valid, please follow the pattern:\n {pattern}"
        )
        sys.exit(1)
