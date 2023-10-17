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

from git import Repo
import cattrs

from git_policy import *

if os.environ.get("CONFIG_PATH"):
    config = Config(RepositoryEnv(os.environ["CONFIG_PATH"]))
elif Path(".env.local").is_file():
    config = Config(RepositoryEnv(".env.local"))
else:
    config = decouple_config


def main():
    base_branch = open(".git/devops/base_branch", "r").read().strip()
    repo = Repo(".")
    if base_branch != str(repo.active_branch):
        print(f"You must be in '{base_branch}' branch to run this command")
        sys.exit(1)

    JIRA_EMAIL = config("JIRA_EMAIL")
    JIRA_TASKS_EMAIL = config("JIRA_TASKS_EMAIL", default=JIRA_EMAIL)
    JIRA_TOKEN = config("JIRA_TOKEN")
    JIRA_BOARD = config("JIRA_BOARD", default="33")
    JIRA_BASE_URL = config("JIRA_BASE_URL")
    JIRA_TASK_STATUS_VALUE = config("JIRA_TASK_STATUS_VALUE", default="En curso")
    TASKS_TYPES = config(
        "TASKS_TYPES",
        default="feat|fix|bugfix|config|refactor|build|ci|docs|test",
    )
    API_URL = f"/rest/agile/1.0/board/{JIRA_BOARD}/sprint"  # sprints from a board
    API_URL = JIRA_BASE_URL + API_URL
    BASIC_AUTH = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    HEADERS = {"Content-Type": "application/json;charset=iso-8859-1"}
    response = requests.get(API_URL, headers=HEADERS, auth=BASIC_AUTH)
    if response.status_code != 200:
        print(f"Error from Jira: {response.status_code}")
        sys.exit(1)

    # try:
    #     all_sprints = cattrs.structure(response.json(), Sprints)
    # except cattrs.errors.ClassValidationError as ve:
    #     print(f"Incorrect response from: {API_URL}")

    all_sprints = cattrs.structure(response.json(), Sprints)
    sprints = []
    for sprint in all_sprints.values:
        if sprint.state == "active":
            sprints.append(sprint.id)

    current_sprint = sprints[0]
    if len(sprints) > 1:
        my_env = os.environ.copy()
        my_env["GUM_CHOOSE_HEADER"] = f"Choose a sprint:"
        result = subprocess.run(
            ["gum", "choose"] + sprints, stdout=subprocess.PIPE, text=True, env=my_env
        )
        current_sprint = result.stdout.strip()
    elif len(sprints) == 0:
        print("No active sprint found")
        sys.exit(1)

    API_URL = f"/rest/agile/1.0/sprint/{current_sprint}/issue"  # issues from a sprint
    API_URL = JIRA_BASE_URL + API_URL
    BASIC_AUTH = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    HEADERS = {"Content-Type": "application/json;charset=iso-8859-1"}
    response = requests.get(API_URL, headers=HEADERS, auth=BASIC_AUTH)

    if response.status_code != 200:
        print(f"Error from Jira: {response.status_code}")
        sys.exit(1)

    # try:
    #     all_issues = cattrs.structure(response.json(), Issues).issues
    # except cattrs.errors.ClassValidationError as ve:
    #     print(f"Incorrect response from: {API_URL}")

    all_issues = cattrs.structure(response.json(), Issues).issues
    options = {}
    for issue in all_issues:
        if (
            issue.fields.assignee is not None
            and issue.fields.status.name == JIRA_TASK_STATUS_VALUE
            and issue.fields.assignee.emailAddress == JIRA_TASKS_EMAIL
        ):
            options.update({issue.key: issue.fields.summary})

    description = ""
    menu = ["Description", "Type", "Apply and exit"]
    values = {"Task selection": None, "Description": None, "Type": None}
    if len(options) == 0:
        print("No active tasks found")
        sys.exit(1)
    elif len(options) == 1:
        values["Task selection"] = list(options.keys())[0]
        description = list(options.values())[0]
    else:
        menu.insert(0, "Task selection")

    flag = True
    while flag:
        my_env = os.environ.copy()
        my_env["GUM_CHOOSE_HEADER"] = f"Choose a config option:"
        result = subprocess.run(
            ["gum", "choose"] + menu, stdout=subprocess.PIPE, text=True, env=my_env
        )

        match result.stdout.strip():
            case "Task selection":
                my_env = os.environ.copy()
                my_env["GUM_CHOOSE_HEADER"] = f"Choose a task to work on:"
                current_tasks = [f"{k}: {v}" for k, v in options.items()]
                opt = subprocess.run(
                    ["gum", "choose"] + current_tasks,
                    stdout=subprocess.PIPE,
                    text=True,
                    env=my_env,
                )
                values["Task selection"] = opt.stdout.strip().split(":")[0].strip()
                description = options[values["Task selection"]]
            case "Description":
                my_env[
                    "GUM_INPUT_HEADER"
                ] = f"Enter the description (ENTER keeps the default value):"
                my_env["GUM_INPUT_WIDTH"] = "0"
                desc = description
                if desc == "":
                    desc = "Description"
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
                    # print(f"git switch -c {branch_name}")

                    subprocess.run(
                        ["git", "switch", "-c", branch_name],
                        stdout=subprocess.PIPE,
                        text=True,
                    )

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
    main()
