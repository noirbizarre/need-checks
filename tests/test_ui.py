from __future__ import annotations

from typing import get_args

import pytest

from need_checks import types, ui
from tests.factories import GitRefFactory


@pytest.mark.parametrize(
    "ref,expected",
    [
        ("heads/main", f"branch {ui.white('main')}"),
        ("heads/prefixed/branch", f"branch {ui.white('prefixed/branch')}"),
        ("tags/1.2.3", f"tag {ui.white('1.2.3')}"),
        ("pull/42/merge", f"pull request {ui.white('#42')}"),
        ("unknown/ref", f"{ui.white('unknown/ref')}"),
    ],
)
def test_ref_type(ref: str, expected: str):
    gitref = GitRefFactory.build(ref=f"refs/{ref}", object={"sha": "sha1"})
    assert ui.ref_type(gitref) == f"{expected} (sha1)"


@pytest.mark.parametrize("conclusion", get_args(types.Conclusion.__value__))  # type: ignore[attr-defined]
def test_conclusion_icon(conclusion: str):
    assert ui.conclusion_icon(conclusion)
