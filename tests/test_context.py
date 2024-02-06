from pathlib import Path
from typing import Any

import pytest

from need_checks.context import Context, Inputs


def test_target_owner_and_repo():
    inputs = Inputs(repository="owner/repo")

    assert inputs.target_owner == "owner"
    assert inputs.target_repo == "repo"


@pytest.mark.parametrize(
    "value,expected",
    (
        pytest.param("", None, id="empty string"),
        pytest.param("42", 42, id="int as str"),
        pytest.param("null", None, id="null"),
    ),
)
def test_wait_timeout_input(value: str, expected: Any, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("INPUT_WAIT_TIMEOUT", value)

    assert Inputs().wait_timeout == expected


def test_parse_github_composite_docker_action_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    event_path = tmp_path / "event.json"
    event_path.write_text("""{"repository": {"name": "repo"}}""")

    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "me")
    monkeypatch.setenv("GITHUB_JOB", "my-job")
    monkeypatch.setenv("GITHUB_WORKFLOW_REF", "owner/repo/.github/workflows/ci.yml@refs/heads/main")
    monkeypatch.setenv("GITHUB_RUN_ID", "45")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("INPUT_TOKEN", "my-token")
    monkeypatch.setenv("INPUT_CONCLUSIONS", "skipped, cancelled")

    ctx = Context()

    assert ctx.github.repository_owner == "me"
    assert ctx.github.event.repository.name == "repo"
    assert ctx.inputs.token == "my-token"
    assert ctx.inputs.conclusions == ["skipped", "cancelled"]
