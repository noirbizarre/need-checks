from __future__ import annotations

import click

from .context import Context
from .types import CheckRun, GitRef


def header(logo: str, text: str) -> str:
    return f"{logo} {bold(text)}"


def bold(text: str) -> str:
    return click.style(text, fg="white", bold=True)


def white(text: str) -> str:
    return click.style(text, fg="white")


def ref_type(ref: GitRef) -> str:
    sha = f"({ref['object']['sha']})"
    match ref["ref"].removeprefix("refs/").split("/"):
        case ["heads", *parts]:
            return f"branch {white('/'.join(parts))} {sha}"
        case ["tags", tag]:
            return f"tag {white(tag)} {sha}"
        case ["pull", prno, "merge"]:
            pr = f"#{prno}"
            return f"pull request {white(pr)} {sha}"
        case [*parts]:
            return f"{white('/'.join(parts))} {sha}"
    return ""  # Never reached but Mypy is so dumb


def display_inputs(label: str, ctx: Context):
    print(header("📥", label))
    for name, value in ctx.inputs.model_dump().items():
        if name == "token":
            value = f"{value[:3]}**********{value[-3:]}"  # Don't leak credentials
        print(f"  {white(name)}: {value}")


def conclusion_icon(status: str) -> str:
    match status:
        case "success":
            return "✅"
        case "cancelled":
            return "❌"
        case "skipped":
            return "📴"
        case "failure" | "startup_failure":
            return "💥"
        case "timed_out":
            return "⌛"
        case "action_required":
            return "🔏"
        case "neutral":
            return "◾"
        case _:
            return "❓"


def display_checks(label: str, checks: list[CheckRun]):
    print(header("📃", label))
    for check in checks:
        print(f"  {conclusion_icon(check.get('conclusion') or '')} {white(check['name'])}")
