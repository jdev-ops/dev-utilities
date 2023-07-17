#!/usr/bin/env python

import sys
import re
from git import Repo
from decouple import Config, RepositoryEnv

config = Config(RepositoryEnv(".env.local"))

if __name__ == "__main__":
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


def put_as_githook():
    import shutil

    shutil.copy(__file__, ".git/hooks/")
    shutil.move(".git/hooks/pre_commit.py", ".git/hooks/pre-commit")
