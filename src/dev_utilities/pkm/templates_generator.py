from jinja2 import Environment, PackageLoader
from slugify import slugify
import os
from pathlib import Path

ad_hoc_input_journal = """
* t
:PROPERTIES:
:heading: 3
:input: [[{{ input }}]]
:producer:
:link:
:tags:
:END:
"""

reference_journal = """
* t
:PROPERTIES:
:heading: 3
:reference: [[{{ input }}]]
:link:
:tags:
:END:
"""

quote_input_journal = """
* t
:PROPERTIES:
:heading: 3
:input: [[{{ input }}]]
:producer:
:tags:
:END:
"""

refer_back_input_page = """
#+input: [[{{ input }}]]
#+producer:
#+link:
#+tags: 
"""

def get_trigger(prefix, value, size=1):
    original_value = value
    value = value.lower().split(" ")
    result = [prefix]
    for word in value:
        if len(word) > 2:
            result.append(word[0])
    if len(result) == 1:
        result.append(value[0][0])
    temp = "".join(result)
    current_size = len(temp)
    if current_size < size:
        extra = value[0][1: size - current_size + 1]
        # print(f"Extra to put for {original_value}: {extra}")
        result.insert(2, extra)
        temp = "".join(result)
    return temp


def main():
    env = Environment(trim_blocks=True)
    env2 = Environment(
        loader=PackageLoader("dev_utilities.pkm", "data/jinja2-templates"),
    )
    inputs_to_refer_back = ["books", "PDFs", "courses"]
    inputs_ad_hoc = ["articles", "videos", "podcasts", ]
    references = ["software", "website", "course",
                  "documentation", "presentation",
                  "source data", "expert", "opinion/POV",
                  "best practice", "how to guide/tutorial",
                  "design guide", "list"]
    extra = ["quotes"]
    graph = {
        "inputs_to_refer_back": {
            "prefix": "ji",
            "length": 3,
            "values": inputs_to_refer_back
        },
        "inputs_ad_hoc": {
            "prefix": "i",
            "length": 3,
            "values": inputs_ad_hoc + extra
        },
        "references": {
            "prefix": "r",
            "length": 3,
            "values": references
        }
    }
    triggers = set()
    templates = []
    for section, details in graph.items():
        prefix = details["prefix"]
        for value in details["values"]:
            slugified_value = slugify(value)
            context = {"input": value}
            template = quote_input_journal
            match section:
                case "inputs_to_refer_back":
                    template = refer_back_input_page
                case "inputs_ad_hoc":
                    template = ad_hoc_input_journal
                case "references":
                    template = reference_journal

            snippet_template =env.from_string(template.strip())
            output=snippet_template.render(context)
            file_path= f"{os.getenv("ESPANSO_TEMPLATES")}/{prefix}_{slugified_value}.org"
            open(file_path, "w").write(output)
            file_name = f"{prefix}_{slugified_value}.org"
            trigger = get_trigger(prefix, value, details["length"])
            if trigger in triggers:
                raise ValueError(f"Duplicate trigger found: {trigger}")
            triggers.add(trigger)
            espanso_context = {
                "trigger": f"{trigger}",
                "file_name": file_name
            }
            templates.append(espanso_context)
    espanso_template = env2.get_template("pkm.yml.jinja")
    espanso_output = espanso_template.render({
        "templates": templates
    })
    espanso_match_path = Path("~/.config/espanso/match/pkm.yml").expanduser()
    open(espanso_match_path, "w").write(espanso_output)
