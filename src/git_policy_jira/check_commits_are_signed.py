#!/usr/bin/env python

import sys
import subprocess
import os
from pathlib import Path
from decouple import config as decouple_config
from decouple import Config, RepositoryEnv

if os.environ.get("CONFIG_PATH"):
    config = Config(RepositoryEnv(os.environ["CONFIG_PATH"]))
elif Path(".env.local").is_file():
    config = Config(RepositoryEnv(".env.local"))
else:
    config = decouple_config

git_executable = ["git"]

SIG_COMMIT = config("SIG_COMMIT", default=None)
ALLOWED_SIGNERS_FILE = config("ALLOWED_SIGNERS_FILE", default=None)
ACTIVE_EMAIL = config("ACTIVE_EMAIL", default=None)
ACTIVE_SIGNING_KEY = config("ACTIVE_SIGNING_KEY", default=None)

JIRA_EMAIL = config("JIRA_EMAIL", default=None)
JIRA_TASKS_EMAIL = config("JIRA_TASKS_EMAIL", default=JIRA_EMAIL)

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

def main():

    CHECK_SIGNED_COMMITS = config("CHECK_SIGNED_COMMITS", cast=bool, default=True)
    if not CHECK_SIGNED_COMMITS:
        sys.exit(0)

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
            cmd = git_executable + [
                "show",
                "-s",
                "--format=%ae",
                sha,
            ]

            res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)

            res = res.stdout.strip().split("\n")
            if JIRA_TASKS_EMAIL not in res:
                print(f"`{sha}` is not my commit, skipping")
                continue

            cmd = git_executable + [
                "show",
                sha,
            ]

            res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)

            res = res.stdout.strip().split("\n")
            if res[1].startswith("Merge:"):
                print(f"`{sha}` is a merge commit, skipping")
                continue

            print(f"Verifying commit {sha}")
            try:
                cmd = git_executable + ["verify-commit", "-v", sha]
                subprocess.check_output(cmd)
            except subprocess.CalledProcessError as e:
                print(f"Commit {sha} is not signed")
                sys.exit(1)
