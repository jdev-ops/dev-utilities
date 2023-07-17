#!/usr/bin/env python

import sys
import subprocess
from decouple import Config, RepositoryEnv

config = Config(RepositoryEnv(".env.local"))

git_executable = ["git"]

SIG_COMMIT = config("SIG_COMMIT")
ALLOWED_SIGNERS_FILE = config("ALLOWED_SIGNERS_FILE")
ACTIVE_EMAIL = config("ACTIVE_EMAIL")
ACTIVE_SIGNING_KEY = config("ACTIVE_SIGNING_KEY")

try:
    subprocess.check_output(["git", "config", "--get", "commit.gpgsign"])
except subprocess.CalledProcessError as e:
    if SIG_COMMIT:
        git_executable += ["--config-env=commit.gpgsign=SIG_COMMIT"]

try:
    subprocess.check_output(["git", "config", "--get", "gpg.ssh.allowedSignersFile"])
except subprocess.CalledProcessError as e:
    if ALLOWED_SIGNERS_FILE:
        git_executable += [
            "--config-env=gpg.ssh.allowedSignersFile=ALLOWED_SIGNERS_FILE"
        ]

try:
    subprocess.check_output(["git", "config", "--get", "user.email"])
except subprocess.CalledProcessError as e:
    if ACTIVE_EMAIL:
        git_executable += ["--config-env=user.email=ACTIVE_EMAIL"]

try:
    subprocess.check_output(["git", "config", "--get", "user.signingKey"])
except subprocess.CalledProcessError as e:
    if ACTIVE_SIGNING_KEY:
        git_executable += ["--config-env=user.signingKey=ACTIVE_SIGNING_KEY"]

if __name__ == "__main__":
    for line in sys.stdin:
        local_ref, local_sha1, remote_ref, remote_sha1 = line.strip().split()
        if remote_sha1.startswith("000000000000000"):
            sys.exit(0)
        cmd = git_executable + [
            "log",
            "--format=format:%H",
            local_sha1,
            f"^{remote_sha1}",
        ]
        message = subprocess.check_output(cmd)
        for sha in message.decode("UTF-8").split("\n"):
            try:
                cmd = git_executable + ["verify-commit", "-v", sha]
                res = subprocess.check_output(cmd)
            except subprocess.CalledProcessError as e:
                print(e)
                sys.exit(1)


def put_as_githook():
    import shutil

    shutil.copy(__file__, ".git/hooks/")
    shutil.move(".git/hooks/pre_push.py", ".git/hooks/pre-push")
