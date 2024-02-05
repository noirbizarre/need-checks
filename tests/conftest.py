from __future__ import annotations

import json
from dataclasses import dataclass
from http.client import HTTPMessage, HTTPResponse
from io import StringIO
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import quote_plus

import pytest
from fastcore.net import ExceptionsHTTP
from ghapi.all import GhApi

from need_checks.context import Context, read_context
from need_checks.types import CheckRunList, Job, JobList, WorkflowRun, WorkflowRunList
from tests.factories import CheckRunFactory, JobFactory, WorkflowRunFactory

if TYPE_CHECKING:
    from urllib.request import Request

    from ghapi.core import _GhVerb as GhVerb
    from ghapi.core import _GhVerbGroup as GhVerbGroup
    from pytest_mock import MockerFixture


@pytest.fixture
def owner() -> str:
    return "owner"


@pytest.fixture
def repo() -> str:
    return "repo"


type Endpoint = tuple[str, str]  # type: ignore[valid-type]


class MockGhApi:
    def __init__(
        self,
        mocker: MockerFixture,
        *args,
        owner: str | None = None,
        repo: str | None = None,
        **kwargs,
    ) -> None:
        print(f"GhApi, {args=}, {kwargs=}, {owner=}, {repo=}")
        self.mocker = mocker
        self.mocker.patch("fastcore.net.urlopen", wraps=self.mock_urlopen)
        self.api = GhApi(*args, **kwargs)
        self.responses: dict[Endpoint, Any] = {}
        self.calls: dict[Endpoint, list[Any]] = {}
        self.owner = owner
        self.repo = repo

    def __getattr__(self, name):
        if not (group := self.api.groups.get(name)):
            raise AttributeError(f"GhApi.{name} group not found")
        return MockVerbGroup(self, group)

    def mock_urlopen(self, request: Request, **kwargs):
        endpoint = (str(request.method), str(request.full_url))

        if (expected := self.responses.get(endpoint)) is None:
            raise ValueError(f"Unexpected GhApi call: {request.method} {request.full_url}")

        response = HTTPResponse(self.mocker.Mock())
        headers = {}

        match expected:
            case tuple((list(responses), dict(hds))):
                expected = responses[len(self.calls)]
                headers = hds
            case list():
                expected = expected[len(self.calls)]

        mock_args: dict[str, Any] = {}
        match expected:
            case dict():
                mock_args["return_value"] = json.dumps(expected).encode()
            case Exception():
                mock_args["side_effect"] = expected

        self.mocker.patch.object(response, "read", **mock_args)

        if response.headers is None:
            response.headers = HTTPMessage()
        for key, value in headers.items():
            response.headers.add_header(key, value)
        calls = self.calls.setdefault(endpoint, [])
        calls.append((request, response))

        return response


@dataclass
class MockVerbGroup:
    mock: MockGhApi
    group: GhVerbGroup

    def __getattr__(self, name):
        verb = getattr(self.group, name)
        return MockVerb(self.mock, verb)


@dataclass
class MockVerb:
    mock: MockGhApi
    verb: GhVerb

    def __call__(self, *args: Any, **kwargs: Any) -> MockVerbCall:
        return MockVerbCall(self.mock, self.verb, args, kwargs)


@dataclass
class MockVerbCall:
    mock: MockGhApi
    verb: GhVerb
    args: tuple[Any]
    kwargs: dict[str, Any]

    def __post_init__(self):
        for var in "owner", "repo":
            if var not in self.kwargs:
                self.kwargs[var] = getattr(self.mock, var)

    @property
    def endpoint(self) -> tuple[str, str]:
        path = self.verb.path.format(*self.args, **self.kwargs)
        url = f"{self.mock.api.gh_host}{path}"
        if any(p in self.kwargs for p in self.verb.params):
            qs = "&".join(
                f"{p}={quote_plus(self.kwargs[p])}" for p in self.verb.params if p in self.kwargs
            )
            url = "?".join((url, qs))
        return (self.verb.verb.upper(), url)

    def returns(self, data):
        self.mock.responses[self.endpoint] = data

    def error(self, code: int, message: str | None = None):
        cls = ExceptionsHTTP[code]
        url = self.endpoint[1]
        error = cls(url, {}, StringIO(), msg=message)
        self.mock.responses[self.endpoint] = error


@pytest.fixture
def mock_api(owner: str, repo: str, mocker: MockerFixture) -> MockGhApi:
    return MockGhApi(mocker, owner=owner, repo=repo)


@pytest.fixture
def ctx() -> Context:
    ctx = read_context()
    ctx.github.repository_owner = "owner"
    ctx.github.event.repository.name = "repo"
    return ctx


@pytest.fixture
def current_job(ctx: Context) -> Job:
    ctx.github.job = "my-job"
    return JobFactory.build(name=ctx.github.job, status="in_progress")


class MockWorkflow(Protocol):
    def __call__(self, *jobs: Job, ref: str, current: bool = False, **kwargs) -> WorkflowRun:
        ...


@pytest.fixture
def mock_checks(mock_api: MockGhApi, ctx: Context) -> MockWorkflow:
    def fixture(
        *jobs: Job,
        ref: str = "refs/heads/main",
        current: bool = False,
        repository: str = "owner/repo",
        file="ci.yml",
        **kwargs,
    ) -> WorkflowRun:
        owner, repo = repository.split("/", 1)
        workflow_run = WorkflowRunFactory.build(
            path=f".github/workflows/{file}", repository__full_name=repository, **kwargs
        )

        if current:
            ctx.github.run_id = workflow_run["id"]
            ctx.github.workflow_ref = f"{repository}/{workflow_run['path']}@{ref}"

        mock_api.actions.list_jobs_for_workflow_run(run_id=workflow_run["id"]).returns(
            JobList(total_count=len(jobs), jobs=list(jobs))
        )
        mock_api.actions.list_workflow_runs(
            workflow_id=file,
            head_sha=workflow_run["head_sha"],
        ).returns(WorkflowRunList(total_count=1, workflow_runs=[workflow_run]))

        checks = [
            CheckRunFactory.build(
                name=job["name"],
                status=job["status"],
                conclusion=job["conclusion"],
                check_suite={"id": workflow_run["check_suite_id"]},
            )
            for job in jobs
        ]
        mock_api.checks.list_for_ref(owner=owner, repo=repo, ref=ref).returns(
            CheckRunList(total_count=len(checks), check_runs=checks)
        )
        return workflow_run

    return fixture


@pytest.fixture
def mock_workflow(mock_api: MockGhApi, ctx: Context) -> MockWorkflow:
    def fixture(
        *jobs: Job,
        ref: str = "refs/heads/main",
        current: bool = False,
        repository: str = "owner/repo",
        file="ci.yml",
        **kwargs,
    ) -> WorkflowRun:
        owner, repo = repository.split("/", 1)
        workflow_run = WorkflowRunFactory.build(
            path=f".github/workflows/{file}", repository__full_name=repository, **kwargs
        )
        if current:
            ctx.github.run_id = workflow_run["id"]
            ctx.github.workflow_ref = f"{repository}/{workflow_run['path']}@{ref}"
        mock_api.actions.list_jobs_for_workflow_run(run_id=workflow_run["id"]).returns(
            JobList(total_count=len(jobs), jobs=list(jobs))
        )
        mock_api.actions.list_workflow_runs(
            workflow_id=file,
            head_sha=workflow_run["head_sha"],
        ).returns(WorkflowRunList(total_count=1, workflow_runs=[workflow_run]))
        mock_api.actions.list_workflow_runs(
            workflow_id=workflow_run["workflow_id"],
            head_sha=workflow_run["head_sha"],
        ).returns(WorkflowRunList(total_count=1, workflow_runs=[workflow_run]))
        checks = [
            CheckRunFactory.build(
                name=job["name"],
                status=job["status"],
                conclusion=job["conclusion"],
                check_suite={"id": workflow_run["check_suite_id"]},
            )
            for job in jobs
        ]
        mock_api.checks.list_for_ref(owner=owner, repo=repo, ref=ref).returns(
            CheckRunList(total_count=len(checks), check_runs=checks)
        )
        return workflow_run

    return fixture
