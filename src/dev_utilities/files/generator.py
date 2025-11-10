import ast
import json
import os
import subprocess
from abc import ABC
from pathlib import Path

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


class UX(ABC):
    def choose(self, options, header="Choose"):
        pass

    def multiple_choose(self, options, header="Choose"):
        pass

    def input(self, placeholder):
        pass


class GumUX(UX):
    def choose(self, options, header="Choose"):
        if len(options) == 1:
            return options[0]
        menu = [f'"{t}"' for t in options]
        menu = " ".join(menu)
        current_selection = subprocess.check_output(
            [f"gum choose {menu}"], text=True, shell=True
        ).strip()
        return current_selection

    def multiple_choose(self, options, header="Choose"):
        menu = [f'"{t}"' for t in options]
        menu = " ".join(menu)
        selection_from_choices = subprocess.check_output(
            [f'gum choose --no-limit --header "{header}" {menu}'],
            text=True,
            shell=True,
        ).strip()
        return selection_from_choices

    def input(self, placeholder):
        value = subprocess.check_output(
            [f'gum input --placeholder "{placeholder}"'],
            text=True,
            shell=True,
        ).strip()
        return value


class RofiUX(UX):
    def choose(self, options, header="Choose"):
        if len(options) == 1:
            return options[0]
        menu = [f"{t}" for t in options]
        menu = "\n".join(menu)
        current_selection = subprocess.check_output(
            ["rofi -dmenu"], text=True, shell=True, input=menu
        ).strip()
        return current_selection

    def multiple_choose(self, options, header="Choose"):
        if len(options) == 1:
            return options[0]
        menu = [f"{t}" for t in options]
        menu = "\n".join(menu)
        current_selection = subprocess.check_output(
            ["rofi -dmenu -multi-select"], text=True, shell=True, input=menu
        ).strip()
        return current_selection

    def input(self, placeholder):
        value = subprocess.check_output(
            [f'rofi -dmenu -p "{placeholder}"'],
            text=True,
            shell=True,
        ).strip()
        return value


# Traverse all the branch of a specified path
# https://www.w3schools.com/python/ref_os_walk.asp
def _on_error(err):
    print(f"Error with: {err}")


class FileStructureGenerator:
    def __init__(self, templates: list[str]):
        self.templates = templates
        self.env = Environment(trim_blocks=True)

        ux_type = config("PROJECTS_GENERATOR_UI", default="gum")
        match ux_type:
            case "gum":
                self.ux = GumUX()
            case "rofi":
                self.ux = RofiUX()

    def run(self):
        template = self.select_template()
        base_path = Path(template)
        last_selection_path = Path(f"{template}-last-selection.json")
        choices_path = Path(f"{template}-choices.json")
        choices = json.loads(open(choices_path).read()) if choices_path.exists() else {}
        options = []
        context = {}
        load_last_selection_option = "Use parameters from last execution"
        exist_load_last_selection_option = True
        apply = "Apply selected parameters"
        exist_apply = False
        if last_selection_path.exists():
            options.append(load_last_selection_option)
        variables = self.get_vars(base_path, self.env)
        variables_entries = {f"Set '{var}' param": var for var in variables}
        options.extend(variables_entries.keys())
        current_selection = ""
        while current_selection not in [apply, load_last_selection_option]:
            current_selection = self.ux.choose(options=options)
            if current_selection in variables_entries.keys():
                param_to_set = variables_entries[current_selection]
                if param_to_set in choices:
                    local_options = choices[param_to_set]
                    selection_from_choices = self.ux.multiple_choose(
                        local_options, header=f"Setting {param_to_set}"
                    )
                    if selection_from_choices:
                        context[param_to_set] = [
                            ast.literal_eval(literal_str)
                            for literal_str in selection_from_choices.split("\n")
                        ]
                        if exist_load_last_selection_option:
                            options = options[1:]
                            exist_load_last_selection_option = False
                else:
                    value = self.ux.input(f"Enter {param_to_set}")
                    if value:
                        context[param_to_set] = value
                        if exist_load_last_selection_option:
                            options = options[1:]
                            exist_load_last_selection_option = False
                if (
                    variables.difference(set(context.keys())) == set()
                    and not exist_apply
                ):
                    options.append(apply)
                    exist_apply = True
        if current_selection == load_last_selection_option:
            context = json.loads(open(last_selection_path).read())
        base_dest = Path(os.getcwd()) / Path(
            self.env.from_string(base_path.parts[-1]).render(context)
        )
        self.generate(base_path, base_dest, self.env, context)
        open(last_selection_path, "w").write(json.dumps(context))

    def generate(
        self, base_path: Path, base_dest: Path, env: Environment, context: dict
    ):
        for root, dirs, files in os.walk(base_path, onerror=_on_error, topdown=True):
            target_path = env.from_string(root).render(context)
            target_path = Path(target_path)
            rest = target_path.parts[len(base_path.parts) :]
            target_path = Path(*base_dest.parts + rest)

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
        return self.ux.choose(self.templates)


def main():
    projects_templates_path = Path(config("PROJECTS_TEMPLATES_PATH"))
    templates = json.loads(open(projects_templates_path).read())
    generator = FileStructureGenerator(templates)
    generator.run()


if __name__ == "__main__":
    typer.run(main)
