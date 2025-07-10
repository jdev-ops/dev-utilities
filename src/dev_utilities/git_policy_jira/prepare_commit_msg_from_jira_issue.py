#!/usr/bin/env python

import os
import sys
from pathlib import Path

from decouple import Config, RepositoryEnv
from decouple import config as decouple_config
from git import Repo
from slugify import slugify

CONFIG_WORKING_DIR = os.environ.get("CONFIG_WORKING_DIR", ".")

if os.environ.get("CONFIG_PATH"):
    config = Config(RepositoryEnv(os.environ["CONFIG_PATH"]))
elif Path(f"{CONFIG_WORKING_DIR}/.env.local").is_file():
    config = Config(RepositoryEnv(f"{CONFIG_WORKING_DIR}/.env.local"))
else:
    config = decouple_config


def main():
    if len(sys.argv) > 2:  # amended commit
        print("Amending commit, skipping")
        sys.exit(0)
    else:
        repo = Repo(".")
        branch_name = str(repo.active_branch)
        if os.path.exists(f"{CONFIG_WORKING_DIR}/.git/devops/.{slugify(branch_name)}"):
            template = open(
                f"{CONFIG_WORKING_DIR}/.git/devops/.{slugify(branch_name)}"
            ).read()
        else:
            template = f""
        open(sys.argv[-1], "w").write(template)
        sys.exit(0)
