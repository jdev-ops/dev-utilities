# env = Environment()
# # ast = env.parse('{% set foo = 42 %}{{ bar + foo }}')
# str1 = """
# {{ foo }}
# """
# str2 = """
# {% for item in navigation %}
#         <li><a href="{{ item.href }}">{{ item.caption }}</a></li>
# {% endfor %}
# """
# ast = env.parse(str2)
# res = meta.find_undeclared_variables(ast)
# print(res)
import ast
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from decouple import Config, RepositoryEnv
from decouple import config as decouple_config
from jinja2 import Environment, meta

CONFIG_WORKING_DIR = os.environ.get("CONFIG_WORKING_DIR", "../..")

if os.environ.get("CONFIG_PATH"):
    config = Config(RepositoryEnv(os.environ["CONFIG_PATH"]))
elif Path(f"{CONFIG_WORKING_DIR}/.env.local").is_file():
    config = Config(RepositoryEnv(f"{CONFIG_WORKING_DIR}/.env.local"))
else:
    config = decouple_config


# Travers all the branch of a specified path
# https://www.w3schools.com/python/ref_os_walk.asp
def _on_error(err):
    print(f"Error with: {err}")


class FileStructureGenerator:
    def __init__(self, templates: list[str]):
        self.templates = templates
        self.env = Environment(trim_blocks=True)

    def run(self):
        base_path = Path(self.select_template())
        last_selection_path = base_path.parent / "last-selection.json"
        choices_path = base_path.parent / "choices.json"
        choices = json.loads(open(choices_path).read()) if choices_path.exists() else {}
        options = []
        context = {}
        load_last_selection_option = "Use parameters from last execution"
        apply = "Apply selected parameters"
        if last_selection_path.exists():
            options.append(load_last_selection_option)
        variables = self.get_vars(base_path, self.env)
        variables_entries = {f"Set '{var}' param": var for var in variables}
        options.extend(variables_entries.keys())
        current_selection = ""
        while current_selection not in [apply, load_last_selection_option]:
            menu = [f'"{t}"' for t in options]
            menu = " ".join(menu)
            current_selection = subprocess.check_output(
                [f"gum choose {menu}"], text=True, shell=True
            ).strip()
            if current_selection in variables_entries.keys():
                param_to_set = variables_entries[current_selection]
                if param_to_set in choices:
                    local_options = choices[param_to_set]
                    menu = [f'"{t}"' for t in local_options]
                    menu = " ".join(menu)
                    selection_from_choices = subprocess.check_output(
                        [
                            f'gum choose --no-limit --header "Setting {param_to_set}" {menu}'
                        ],
                        text=True,
                        shell=True,
                    ).strip()
                    if selection_from_choices:
                        context[param_to_set] = [
                            ast.literal_eval(literal_str)
                            for literal_str in selection_from_choices.split("\n")
                        ]
                        options = []
                        options.extend(variables_entries.keys())
                else:
                    value = subprocess.check_output(
                        [f"gum input --placeholder {param_to_set}"],
                        text=True,
                        shell=True,
                    ).strip()
                    if value:
                        context[param_to_set] = value
                        options = []
                        options.extend(variables_entries.keys())
                if variables.difference(set(context.keys())) == set():
                    options.append(apply)
        if current_selection == load_last_selection_option:
            context = json.loads(open(last_selection_path).read())
        base_dest = Path(self.env.from_string(base_path.parts[-1]).render(context))
        self.generate(base_path, base_dest, self.env, context)

    def generate(
        self, base_path: Path, base_dest: Path, env: Environment, context: dict
    ):
        for root, dirs, files in os.walk(base_path, onerror=_on_error, topdown=True):
            target_path = base_dest / env.from_string(root).render(context)
            os.makedirs(target_path, exist_ok=True)
            for filename in files:
                rendered_filename = env.from_string(filename).render(context)
                rendered_filename = target_path / rendered_filename
                file_content = open(Path(root) / filename, "r").read()
                file_content = env.from_string(file_content).render(context)
                open(rendered_filename, "w").write(file_content)

    def get_vars(self, base_path: Path, env: Environment):
        result = set()
        for root, dirs, files in os.walk(base_path, onerror=_on_error, topdown=True):
            ast = env.parse(root)
            vars_from_root = meta.find_undeclared_variables(ast)
            result.update(vars_from_root)
            for filename in files:
                ast = env.parse(filename)
                vars_from_file_name = meta.find_undeclared_variables(ast)
                file_content = open(Path(root) / filename, "r").read()
                ast = env.parse(file_content)
                vars_from_file_content = meta.find_undeclared_variables(ast)
                result.update(vars_from_file_name)
                result.update(vars_from_file_content)
        return result

    def select_template(self):
        if len(self.templates) == 1:
            return self.templates[0]
        templates = [f'"{t}"' for t in self.templates]
        templates = " ".join(templates)
        return subprocess.check_output(
            [f"gum choose {templates}"], text=True, shell=True
        ).strip()


def main():
    projects_templates_path = Path(config("PROJECTS_TEMPLATES_PATH"))
    templates = json.loads(open(projects_templates_path).read())
    generator = FileStructureGenerator(templates)
    generator.run()


if __name__ == "__main__":
    typer.run(main)
