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

# from git import Repo
import cattrs

from dev_utilities.git_policy_jira import *

CONFIG_WORKING_DIR = os.environ.get("CONFIG_WORKING_DIR", ".")

if os.environ.get("CONFIG_PATH"):
    config = Config(RepositoryEnv(os.environ["CONFIG_PATH"]))
elif Path(f"{CONFIG_WORKING_DIR}/.env.local").is_file():
    config = Config(RepositoryEnv(f"{CONFIG_WORKING_DIR}/.env.local"))
else:
    config = decouple_config

def main(issue_id: Annotated[str, typer.Argument()]):
    DOMAIN_PREFIX = config("DOMAIN_PREFIX")
    JIRA_EMAIL = config("JIRA_EMAIL")
    JIRA_TOKEN = config("JIRA_TOKEN")

    JIRA_BASE_URL = config("JIRA_BASE_URL")
    TASKS_TYPES = config(
        "TASKS_TYPES",
        default="feat|fix|bugfix|config|refactor|build|ci|docs|test",
    )
    PUSH_TO_REMOTE = config("PUSH_TO_REMOTE", cast=bool, default=False)
    SWITCH_TO_NEW_BRANCH = config("SWITCH_TO_NEW_BRANCH", cast=bool, default=False)

    # base_branch = open(".git/devops/base_branch").read().strip()
    # repo = Repo(".")
    # if base_branch != str(repo.active_branch):
    #     print(base_branch)
    #     print(repo.active_branch)
    #     print(f"You must be in '{base_branch}' branch to run this command")
    #     sys.exit(1)

    base_branch = open(f"{CONFIG_WORKING_DIR}/.git/devops/base_branch").read().strip()

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

                    print(f"Creating branch {branch_name} from {base_branch}")

                    subprocess.run(
                        ["git", "branch", branch_name, base_branch],
                        stdout=subprocess.PIPE,
                        text=True,
                    )

                    if SWITCH_TO_NEW_BRANCH:
                        subprocess.run(
                            ["git", "switch", branch_name],
                            stdout=subprocess.PIPE,
                            text=True,
                        )

                    if PUSH_TO_REMOTE:
                        subprocess.run(
                            ["git", "push", "-u", "origin", branch_name],
                            stdout=subprocess.PIPE,
                            text=True,
                        )

                    if not os.path.exists(f"{CONFIG_WORKING_DIR}/.git/devops"):
                            os.makedirs(f"{CONFIG_WORKING_DIR}/.git/devops")
                    open(f"{CONFIG_WORKING_DIR}/.git/devops/.{slugify(branch_name)}", "w").write(
                        f"""{values['Type']}: [{values['Task selection']}] {description}

Jira Ticket Link: {JIRA_BASE_URL}/browse/{values['Task selection']}
"""
                    )
                    flag = False


if __name__ == "__main__":
    typer.run(main)
