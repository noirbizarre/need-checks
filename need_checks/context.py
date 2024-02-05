from __future__ import annotations

import os
from dataclasses import dataclass

from fastcore.basics import AttrDict
from ghapi.actions import context_github
from pydantic import BaseModel, field_validator

from need_checks.types import Conclusion


class Inputs(BaseModel):
    token: str = ""
    repository: str = ""
    ref: str = ""
    workflow: str | None = None
    wait: bool = False
    wait_interval: int = 60
    wait_timeout: int | None = None
    conclusions: list[Conclusion] = ["success", "skipped"]

    @field_validator("conclusions", mode="before")
    @classmethod
    def comma_separated_list(cls, value: str | list[Conclusion]):
        if isinstance(value, str):
            return [v.strip() for v in value.split(",")]
        return value

    @property
    def target_owner(self) -> str:
        owner, _ = self.repository.split("/", 1)
        return owner

    @property
    def target_repo(self) -> str:
        _, repo = self.repository.split("/", 1)
        return repo


class Repository(AttrDict):
    name: str


class Event(AttrDict):
    repository: Repository


class GithubContext(AttrDict):
    repository_owner: str
    job: str
    run_id: int
    event: Event
    workflow_ref: str


@dataclass
class Context:
    github: GithubContext
    inputs: Inputs


def read_context() -> Context:
    inputs = Inputs.model_validate_json(os.getenv("CONTEXT_INPUTS", "{}"))
    return Context(github=context_github, inputs=inputs)
