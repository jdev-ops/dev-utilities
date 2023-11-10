#!/usr/bin/env python

import sys
import os
from git import Repo
from slugify import slugify

if __name__ == "__main__":
    if len(sys.argv) > 2:  # amended commit
        print("Amending commit, skipping")
        sys.exit(0)
    else:
        repo = Repo(".")
        branch_name = str(repo.active_branch)
        if os.path.exists(f".git/devops/.{slugify(branch_name)}"):
            template = open(f".git/devops/.{slugify(branch_name)}").read()
        else:
            template = f""
        open(sys.argv[-1], "w").write(template)
        sys.exit(0)


def put_as_githook():
    import shutil

    shutil.copy(__file__, ".git/hooks/")
    shutil.move(".git/hooks/prepare_commit_msg.py", ".git/hooks/prepare-commit-msg")
