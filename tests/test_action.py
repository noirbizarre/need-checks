from __future__ import annotations

from base64 import b64encode
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from need_checks import action
from need_checks.errors import ActionError, RequirementsNotMet, Timeout, UnknownRef
from need_checks.types import CheckRunList, Content, WorkflowRunList
from tests.factories import (
    CheckRunFactory,
    ContentFactory,
    GitRefFactory,
    JobFactory,
    WorkflowRunFactory,
)

if TYPE_CHECKING:
    from need_checks.context import Context
    from need_checks.types import Job
    from tests.conftest import MockGhApi, MockWorkflow


def as_content(content: str) -> Content:
    encoded = b64encode(content.encode("utf8")).decode("utf8")
    return ContentFactory.build(content=encoded)


def test_get_ref_main(mock_api: MockGhApi, owner: str, repo: str):
    mock_api.git.get_ref(ref="main").error(404)
    mock_api.git.get_ref(ref="tags/main").error(404)
    mock_api.git.get_ref(ref="heads/main").returns(GitRefFactory.build(ref="refs/heads/main"))
    ref = action.get_ref(mock_api.api, owner, repo, "main")
    assert ref["ref"] == "refs/heads/main"


def test_get_ref_heads_main(mock_api: MockGhApi, owner: str, repo: str):
    mock_api.git.get_ref(ref="heads/main").returns(GitRefFactory.build(ref="refs/heads/main"))

    ref = action.get_ref(mock_api.api, owner, repo, "heads/main")

    assert ref["ref"] == "refs/heads/main"


def test_get_ref_heads_main_with_refs_prefix(mock_api: MockGhApi, owner: str, repo: str):
    mock_api.git.get_ref(ref="heads/main").returns(GitRefFactory.build(ref="refs/heads/main"))

    ref = action.get_ref(mock_api.api, owner, repo, "refs/heads/main")

    assert ref["ref"] == "refs/heads/main"


def test_get_ref_tag(mock_api: MockGhApi, owner: str, repo: str):
    mock_api.git.get_ref(ref="1.2.3").error(404)
    mock_api.git.get_ref(ref="tags/1.2.3").returns(GitRefFactory.build(ref="refs/tags/1.2.3"))

    ref = action.get_ref(mock_api.api, owner, repo, "1.2.3")

    assert ref["ref"] == "refs/tags/1.2.3"


def test_get_ref_branch(mock_api: MockGhApi, owner: str, repo: str):
    mock_api.git.get_ref(ref="branch").error(404)
    mock_api.git.get_ref(ref="tags/branch").error(404)
    mock_api.git.get_ref(ref="heads/branch").returns(GitRefFactory.build(ref="refs/heads/branch"))

    ref = action.get_ref(mock_api.api, owner, repo, "branch")

    assert ref["ref"] == "refs/heads/branch"


def test_get_ref_unknown(mock_api: MockGhApi, owner: str, repo: str):
    mock_api.git.get_ref(ref="main").error(404)
    mock_api.git.get_ref(ref="tags/main").error(404)
    mock_api.git.get_ref(ref="heads/main").error(404)

    with pytest.raises(UnknownRef):
        action.get_ref(mock_api.api, owner, repo, "main")


def test_find_current_job(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    mock_workflow(current_job, *JobFactory.batch(2), ref="ref/heads/main", current=True)

    assert action.get_current_job(mock_api.api, ctx).get("id") == current_job["id"]


def test_find_current_job_with_name(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    ctx.inputs.repository = "owner/repo"
    current_job["name"] = "Not the job ID"
    mock_workflow(current_job, *JobFactory.batch(2), ref="refs/heads/main", current=True)
    workflow = dedent(
        f"""\
        jobs:
            {ctx.github.job}:
                name: {current_job["name"]}
        """
    )
    content = as_content(workflow)
    mock_api.repos.get_content(
        owner="owner",
        repo="repo",
        path=".github/workflows/ci.yml",
        ref="heads/main",
    ).returns(content)

    assert action.get_current_job(mock_api.api, ctx).get("id") == current_job["id"]


def test_fetch_workflow(mock_api: MockGhApi):
    ref = "owner/repo/.github/workflows/my-workflow.yml@refs/heads/my_branch"
    workflow = "name: my workflow"
    content = as_content(workflow)
    mock_api.repos.get_content(
        owner="owner",
        repo="repo",
        path=".github/workflows/my-workflow.yml",
        ref="heads/my_branch",
    ).returns(content)

    assert action.fetch_workflow(mock_api.api, ref)["name"] == "my workflow"


def test_fetch_workflow_from_other_repo(mock_api: MockGhApi):
    ref = "octocat/hello-world/.github/workflows/my-workflow.yml@refs/heads/my_branch"
    workflow = "name: my workflow"
    content = as_content(workflow)
    mock_api.repos.get_content(
        owner="octocat",
        repo="hello-world",
        path=".github/workflows/my-workflow.yml",
        ref="heads/my_branch",
    ).returns(content)

    assert action.fetch_workflow(mock_api.api, ref)["name"] == "my workflow"


def test_select_all_checks(mock_api: MockGhApi, ctx: Context):
    ref = GitRefFactory.build(ref="ref")
    ctx.inputs.repository = "owner/repo"
    mock_api.checks.list_for_ref(ref="ref").returns(
        CheckRunList(
            total_count=3,
            check_runs=CheckRunFactory.batch(3, status="completed", conclusion="success"),
        )
    )

    checks = action.select_checks(mock_api.api, ctx, ref, JobFactory.build())

    assert len(checks) == 3


def test_select_all_checks_but_self(mock_api: MockGhApi, ctx: Context, current_job: Job):
    ctx.inputs.repository = "owner/repo"
    ref = GitRefFactory.build(ref="ref")
    checks = CheckRunFactory.batch(3, status="completed", conclusion="success")
    checks.append(CheckRunFactory.build(status=current_job["status"], name=current_job["name"]))
    mock_api.checks.list_for_ref(ref="ref").returns(
        CheckRunList(total_count=len(checks), check_runs=checks)
    )

    selected = action.select_checks(mock_api.api, ctx, ref, current_job)

    assert len(selected) == 3

    for check in selected:
        assert check["name"] != current_job["name"]


def test_select_workflow_checks_but_self(mock_api: MockGhApi, ctx: Context, current_job: Job):
    ctx.inputs.repository = "owner/repo"
    ref = GitRefFactory.build(ref="ref")
    checks = CheckRunFactory.batch(
        3, status="completed", conclusion="success", check_suite={"id": 42}
    )
    checks.append(
        CheckRunFactory.build(
            status=current_job["status"], name=current_job["name"], check_suite={"id": 42}
        )
    )
    mock_api.checks.list_for_suite(check_suite_id=42).returns(
        CheckRunList(total_count=len(checks), check_runs=checks)
    )

    selected = action.select_checks(mock_api.api, ctx, ref, current_job, check_suite=42)

    assert len(selected) == 3

    for check in selected:
        assert check["name"] != current_job["name"]


def test_decide_for_checks_empty(ctx: Context):
    assert action.decide_for_checks(ctx, []) == action.Conclusion.OK


def test_decide_for_checks_ok(ctx: Context):
    checks = CheckRunFactory.batch(2, status="completed", conclusion="success")
    checks.append(CheckRunFactory.build(status="completed", conclusion="skipped"))

    assert action.decide_for_checks(ctx, checks) == action.Conclusion.OK


def test_decide_for_checks_ko(ctx: Context):
    checks = CheckRunFactory.batch(2, status="completed", conclusion="success")
    checks.append(CheckRunFactory.build(status="completed", conclusion="failure"))

    assert action.decide_for_checks(ctx, checks) == action.Conclusion.KO


WAIT_STATUS = "queued", "in_progress", "waiting"


@pytest.mark.parametrize("status", WAIT_STATUS)
def test_decide_for_checks_runnning_and_not_wait(status: str, ctx: Context):
    ctx.inputs.wait = False
    checks = [
        CheckRunFactory.build(status="completed", conclusion="success"),
        CheckRunFactory.build(status=status),
    ]

    assert action.decide_for_checks(ctx, checks) == action.Conclusion.KO


@pytest.mark.parametrize("status", WAIT_STATUS)
def test_decide_for_checks_runnning_and_wait(status: str, ctx: Context):
    ctx.inputs.wait = True
    checks = [
        CheckRunFactory.build(status="completed", conclusion="success"),
        CheckRunFactory.build(status=status),
    ]

    assert action.decide_for_checks(ctx, checks) == action.Conclusion.WAIT


@pytest.mark.parametrize("status", WAIT_STATUS)
def test_decide_for_checks_runnning_but_already_failed(status: str, ctx: Context):
    ctx.inputs.wait = True
    checks = [
        CheckRunFactory.build(status="completed", conclusion="failure"),
        CheckRunFactory.build(status=status),
    ]

    assert action.decide_for_checks(ctx, checks) == action.Conclusion.KO


def test_run_success_same_repo(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    ctx.inputs.repository = "owner/repo"
    ctx.inputs.ref = "1.2.3"

    ref = GitRefFactory.build(ref=f"refs/tags/{ctx.inputs.ref}")
    mock_api.git.get_ref(ref=ctx.inputs.ref).error(404)
    mock_api.git.get_ref(ref=f"tags/{ctx.inputs.ref}").returns(ref)

    mock_workflow(
        current_job,
        *JobFactory.batch(3, status="completed", conclusion="success"),
        ref=ref["ref"],
        current=True,
    )

    action.run(ctx)


def test_run_success_same_repo_with_workflow(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    ctx.inputs.repository = "owner/repo"
    ctx.inputs.ref = "1.2.3"
    ctx.inputs.workflow = "ci.yml"

    ref = GitRefFactory.build(ref=f"refs/tags/{ctx.inputs.ref}")
    mock_api.git.get_ref(ref=ctx.inputs.ref).error(404)
    mock_api.git.get_ref(ref=f"tags/{ctx.inputs.ref}").returns(ref)

    mock_workflow(
        current_job,
        *JobFactory.batch(3, status="completed", conclusion="success"),
        ref=ref["ref"],
        current=True,
        check_suite_id=51,
        head_sha=ref["object"]["sha"],
    )

    action.run(ctx)


def test_same_repo_with_workflow_never_ran(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    ctx.inputs.repository = "owner/repo"
    ctx.inputs.ref = "1.2.3"
    ctx.inputs.workflow = "never.yml"

    ref = GitRefFactory.build(ref=f"refs/tags/{ctx.inputs.ref}")
    mock_api.git.get_ref(ref=ctx.inputs.ref).error(404)
    mock_api.git.get_ref(ref=f"tags/{ctx.inputs.ref}").returns(ref)

    # Current workflow
    mock_workflow(
        current_job,
        current=True,
        ref=ref["ref"],
        check_suite_id=42,
        head_sha=ref["object"]["sha"],
    )

    mock_api.actions.list_workflow_runs(
        workflow_id=ctx.inputs.workflow,
        head_sha=ref["object"]["sha"],
    ).returns(WorkflowRunList(total_count=0, workflow_runs=[]))

    with pytest.raises(RequirementsNotMet):
        action.run(ctx)


def test_same_repo_with_workflow_multiple_runs_and_attempts(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    ctx.inputs.repository = "owner/repo"
    ctx.inputs.ref = "1.2.3"
    ctx.inputs.workflow = "ci.yml"

    ref = GitRefFactory.build(ref=f"refs/tags/{ctx.inputs.ref}")
    mock_api.git.get_ref(ref=ctx.inputs.ref).error(404)
    mock_api.git.get_ref(ref=f"tags/{ctx.inputs.ref}").returns(ref)

    # Current workflow
    mock_workflow(
        current_job,
        current=True,
        ref=ref["ref"],
        head_sha=ref["object"]["sha"],
    )

    workflow_runs = WorkflowRunFactory.batch(
        3,
        path=".github/workflows/ci.yml",
        repository__full_name=ctx.inputs.repository,
        head_sha=ref["object"]["sha"],
    )
    checks = []
    # First workflow is the last with success, 2nd attempt
    workflow_runs[0].update(run_number=4012, run_attempt=2, check_suite_id=53)
    check = CheckRunFactory.build(status="completed", conclusion="success", check_suite={"id": 53})
    mock_api.checks.list_for_suite(owner="owner", repo="repo", check_suite_id=53).returns(
        CheckRunList(total_count=1, check_runs=[check])
    )
    checks.append(check)
    # 2nd run the first failed attempt
    workflow_runs[1].update(run_number=4012, run_attempt=1, check_suite_id=52)
    check = CheckRunFactory.build(status="completed", conclusion="failure", check_suite={"id": 52})
    mock_api.checks.list_for_suite(owner="owner", repo="repo", check_suite_id=52).returns(
        CheckRunList(total_count=1, check_runs=[check])
    )
    checks.append(check)
    # 3rd is the first run which has been canceled
    workflow_runs[2].update(run_number=4011, run_attempt=1, check_suite_id=51)
    check = CheckRunFactory.build(status="completed", conclusion="canceled", check_suite={"id": 51})
    mock_api.checks.list_for_suite(owner="owner", repo="repo", check_suite_id=51).returns(
        CheckRunList(total_count=1, check_runs=[check])
    )
    checks.append(check)

    mock_api.checks.list_for_ref(owner="owner", repo="repo", ref=ref["ref"]).returns(
        CheckRunList(total_count=len(checks), check_runs=checks)
    )

    mock_api.actions.list_workflow_runs(
        workflow_id=ctx.inputs.workflow,
        head_sha=ref["object"]["sha"],
    ).returns(WorkflowRunList(total_count=len(workflow_runs), workflow_runs=workflow_runs))

    action.run(ctx)


def test_run_success_other_repo(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    ctx.inputs.repository = "other/repo"
    ctx.inputs.ref = "1.2.3"

    ref = GitRefFactory.build(ref=f"refs/tags/{ctx.inputs.ref}")
    mock_api.git.get_ref(owner="other", ref=ctx.inputs.ref).error(404)
    mock_api.git.get_ref(owner="other", ref=f"tags/{ctx.inputs.ref}").returns(ref)

    # Current workflow
    mock_workflow(
        current_job, current=True, ref=ref["ref"], check_suite_id=42, head_sha=ref["object"]["sha"]
    )

    # Waited workflow
    mock_workflow(
        *JobFactory.batch(3, status="completed", conclusion="success"),
        ref=ref["ref"],
        check_suite_id=51,
        head_sha=ref["object"]["sha"],
        repository=ctx.inputs.repository,
    )

    action.run(ctx)


def test_run_failed(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    ctx.inputs.repository = "owner/repo"
    ctx.inputs.ref = "1.2.3"

    ref = GitRefFactory.build(ref=f"refs/tags/{ctx.inputs.ref}")
    mock_api.git.get_ref(ref=ctx.inputs.ref).error(404)
    mock_api.git.get_ref(ref=f"tags/{ctx.inputs.ref}").returns(ref)

    mock_workflow(
        current_job,
        *JobFactory.batch(3, status="completed", conclusion="failure"),
        ref=ref["ref"],
        current=True,
        check_suite_id=51,
        head_sha=ref["object"]["sha"],
    )

    with pytest.raises(RequirementsNotMet):
        action.run(ctx)


def test_run_wait_then_success(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    ctx.inputs.repository = "owner/repo"
    ctx.inputs.wait = True
    ctx.inputs.wait_interval = 5
    ctx.inputs.wait_timeout = 10
    ctx.inputs.ref = "1.2.3"

    ref = GitRefFactory.build(ref=f"refs/tags/{ctx.inputs.ref}")
    mock_api.git.get_ref(ref=ctx.inputs.ref).error(404)
    mock_api.git.get_ref(ref=f"tags/{ctx.inputs.ref}").returns(ref)

    jobs = JobFactory.batch(3, status="in_progress", conclusion=None)
    mock_workflow(current_job, *jobs, ref=ref["ref"], current=True)

    def remock(duration: int):
        assert duration == ctx.inputs.wait_interval
        for job in jobs:
            job["conclusion"] = "success"
            job["status"] = "completed"
        mock_workflow(current_job, *jobs, ref=ref["ref"], current=True)

    mock_sleep = mock_api.mocker.patch("need_checks.action.sleep", wraps=remock)

    action.run(ctx)

    assert len(mock_sleep.mock_calls) == 1
    for mock_call in mock_sleep.mock_calls:
        assert mock_call == mock_api.mocker.call(ctx.inputs.wait_interval)


def test_run_wait_then_timeout(
    mock_api: MockGhApi, ctx: Context, current_job: Job, mock_workflow: MockWorkflow
):
    ctx.inputs.repository = "owner/repo"
    ctx.inputs.wait = True
    ctx.inputs.wait_interval = 5
    ctx.inputs.wait_timeout = 10
    ctx.inputs.ref = "1.2.3"

    ref = GitRefFactory.build(ref=f"refs/tags/{ctx.inputs.ref}")
    mock_api.git.get_ref(ref=ctx.inputs.ref).error(404)
    mock_api.git.get_ref(ref=f"tags/{ctx.inputs.ref}").returns(ref)

    mock_workflow(
        current_job,
        *JobFactory.batch(3, status="in_progress"),
        ref=ref["ref"],
        current=True,
    )

    mock_sleep = mock_api.mocker.patch("need_checks.action.sleep", return_value=None)

    with pytest.raises(Timeout):
        action.run(ctx)

    assert len(mock_sleep.mock_calls) == 2
    for mock_call in mock_sleep.mock_calls:
        assert mock_call == mock_api.mocker.call(ctx.inputs.wait_interval)


@pytest.mark.usefixtures("ctx")
def test_main_exit_0(mocker: MockerFixture):
    mocker.patch.object(action, "run")

    runner = CliRunner()
    result = runner.invoke(action.__main__)

    assert result.exit_code == 0


@pytest.mark.usefixtures("ctx")
def test_main_graceful_exit_handled_errors(mocker: MockerFixture):
    mocker.patch.object(action, "run", side_effect=ActionError("KO"))

    runner = CliRunner()
    result = runner.invoke(action.__main__)

    assert result.exit_code == -1
    assert result.output == "❌ KO\n"


@pytest.mark.usefixtures("ctx")
def test_main_exit_unhandled_error_passthrough(mocker: MockerFixture):
    mocker.patch.object(action, "run", side_effect=ValueError("Unhandled error"))

    runner = CliRunner()
    result = runner.invoke(action.__main__, catch_exceptions=True)

    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)
    assert str(result.exception) == "Unhandled error"
