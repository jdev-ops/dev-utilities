import sys
import json
import subprocess
import os

import requests
from requests.auth import HTTPBasicAuth

from slugify import slugify

from pathlib import Path

from decouple import config as decouple_config
from decouple import Config, RepositoryEnv
import typer
from typing import Annotated

from git import Repo
import cattrs

from git_policy_jira import *

if os.environ.get("CONFIG_PATH"):
    config = Config(RepositoryEnv(os.environ["CONFIG_PATH"]))
elif Path(".env.local").is_file():
    config = Config(RepositoryEnv(".env.local"))
else:
    config = decouple_config

def main(issue_id: Annotated[str, typer.Argument()]):
    base_branch = open(".git/devops/base_branch").read().strip()
    repo = Repo(".")
    if base_branch != str(repo.active_branch):
        print(f"You must be in '{base_branch}' branch to run this command")
        sys.exit(1)

    DOMAIN_PREFIX = config("DOMAIN_PREFIX")
    JIRA_EMAIL = config("JIRA_EMAIL")
    JIRA_TOKEN = config("JIRA_TOKEN")

    JIRA_BASE_URL = config("JIRA_BASE_URL")
    TASKS_TYPES = config(
        "TASKS_TYPES",
        default="feat|fix|bugfix|config|refactor|build|ci|docs|test",
    )
    PUSH_TO_REMOTE = config("PUSH_TO_REMOTE", cast=bool, default=False)

    issueIdOrKey = f"{DOMAIN_PREFIX}-{issue_id}"
    API_URL = f"/rest/agile/1.0/issue/{issueIdOrKey}"
    API_URL = JIRA_BASE_URL + API_URL
    BASIC_AUTH = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    HEADERS = {"Content-Type": "application/json;charset=iso-8859-1"}
    response = requests.get(API_URL, headers=HEADERS, auth=BASIC_AUTH)
    if response.status_code != 200:
        print(f"Error from Jira: {response.status_code}")
        sys.exit(1)

    issue = cattrs.structure(response.json(), Issue)

    description = issue.fields.summary
    menu = ["Description", "Type", "Apply and exit"]
    values = {"Description": None, "Type": None, "Task selection": issueIdOrKey}

    flag = True
    while flag:
        my_env = os.environ.copy()
        my_env["GUM_CHOOSE_HEADER"] = f"Choose a config option:"
        result = subprocess.run(
            ["gum", "choose"] + menu, stdout=subprocess.PIPE, text=True, env=my_env
        )
        match result.stdout.strip():
            case "Description":
                my_env[
                    "GUM_INPUT_HEADER"
                ] = f"Enter the description:"
                my_env["GUM_INPUT_WIDTH"] = "0"
                desc = description
                if desc == "":
                    desc = issue.fields.summary
                opt = subprocess.run(
                    ["gum", "input", "--placeholder", desc],
                    stdout=subprocess.PIPE,
                    text=True,
                    env=my_env,
                )
                if opt.stdout.strip() != "":
                    description = opt.stdout.strip()
                values["Description"] = slugify(description)

            case "Type":
                my_env["GUM_CHOOSE_HEADER"] = f"Choose task type:"
                task_types = TASKS_TYPES.split("|")
                opt = subprocess.run(
                    ["gum", "choose"] + task_types,
                    stdout=subprocess.PIPE,
                    text=True,
                    env=my_env,
                    )
                values["Type"] = opt.stdout.strip()
            case "Apply and exit":
                actual = [k for k, v in values.items() if v is None]
                if len(actual) > 0:
                    print(f"Missing values: {actual}")
                    continue
                else:
                    branch_name = f"{values['Type']}/{values['Task selection']}-{values['Description']}"

                    print(f"Creating branch {branch_name}")

                    subprocess.run(
                        ["git", "switch", "-c", branch_name],
                        stdout=subprocess.PIPE,
                        text=True,
                    )

                    if PUSH_TO_REMOTE:
                        subprocess.run(
                            ["git", "push", "-u", "origin", branch_name],
                            stdout=subprocess.PIPE,
                            text=True,
                        )

                    if not os.path.exists(".git/devops"):
                        os.makedirs(".git/devops")
                    open(f".git/devops/.{slugify(branch_name)}", "w").write(
                        f"""{values['Type']}: [{values['Task selection']}] {description}

Jira Ticket Link: {JIRA_BASE_URL}/browse/{values['Task selection']}
"""
                    )
                    flag = False


if __name__ == "__main__":
    typer.run(main)
