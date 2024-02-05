from pathlib import Path

import strictyaml
from strictyaml import YAML

ROOT = Path()

INPUTS = """\
## Inputs

{inputs}
"""

OUTPUTS = """\
## Outputs

{outputs}
"""

START_MARKER = "<!-- auto:start -->\n"
END_MARKER = "<!-- auto:end -->\n"


def inputs_table(inputs: YAML) -> str:
    if not inputs.data:
        return "N/A"
    table = "| Input | Description | Default | Required |\n"
    table += "|-------|-------------|---------|----------|\n"
    for input, spec in inputs.items():
        default = str(spec.get("default", "")) or '""'
        required = spec.get("required", "false")
        description = spec.get("description", "")
        table += f"| `{input}` | {description} | `{default}` | `{required}` |\n"
    return table


def outputs_table(outputs: YAML) -> str:
    if not outputs.data:
        return "N/A"
    table = "| Output | Description |\n"
    table += "|--------|-------------|\n"
    for output, spec in outputs.items():
        table += f"| `{output}` | {spec.get('description', 'TODO: output')} |\n"
    return table


def __main__():
    action = ROOT / "action.yml"
    readme = ROOT / "README.md"
    specs = strictyaml.load(action.read_text())
    start, end = readme.read_text().split(START_MARKER, 1)
    _, end = end.split(END_MARKER, 1)

    readme.write_text(
        "".join(
            (
                start,
                START_MARKER,
                INPUTS.format(inputs=inputs_table(specs.get("inputs", YAML({})))),
                OUTPUTS.format(outputs=outputs_table(specs.get("outputs", YAML({})))),
                END_MARKER,
                end,
            )
        )
    )
