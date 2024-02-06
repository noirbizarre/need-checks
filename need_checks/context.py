from __future__ import annotations

from functools import cached_property
from pathlib import Path
from types import GenericAlias
from typing import Any

from pydantic import BaseModel
from pydantic.fields import Field, FieldInfo, computed_field
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from need_checks.types import Conclusion


class BaseContext(BaseSettings):
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            GithubEnvSettingsSource(settings_cls),
        )


class Inputs(BaseContext):
    token: str = ""
    repository: str = ""
    ref: str = ""
    workflow: str | None = None
    wait: bool = False
    wait_interval: int = 60
    wait_timeout: int | None = None
    conclusions: list[Conclusion] = ["success", "skipped"]

    model_config = SettingsConfigDict(env_prefix="INPUT_")

    @property
    def target_owner(self) -> str:
        owner, _ = self.repository.split("/", 1)
        return owner

    @property
    def target_repo(self) -> str:
        _, repo = self.repository.split("/", 1)
        return repo


class Repository(BaseModel):
    name: str


class Event(BaseModel):
    repository: Repository


class GithubContext(BaseContext):
    repository_owner: str
    job: str
    run_id: int
    event_path: Path
    workflow_ref: str

    model_config = SettingsConfigDict(env_prefix="GITHUB_", extra="ignore")

    @computed_field  # type: ignore[misc]
    @cached_property
    def event(self) -> Event:
        return Event.model_validate_json(self.event_path.read_text())


class Context(BaseContext):
    github: GithubContext = Field(default_factory=GithubContext)
    inputs: Inputs = Field(default_factory=Inputs)


class GithubEnvSettingsSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        # allow comma-separated list parsing
        if value is not None:
            match field.annotation:
                case GenericAlias():
                    value = process_generic_type_value(field.annotation, value)

        return super().prepare_field_value(field_name, field, value, value_is_complex)


def process_generic_type_value(annotation: GenericAlias, value: str) -> Any:
    match annotation.__origin__.__qualname__:
        case list.__qualname__:
            values = [f'"{v.strip()}"' for v in value.split(",")]
            value = f"[{','.join(values)}]"
        case _:
            raise ValueError(f"Unsupported type list[{annotation}")
    return value
