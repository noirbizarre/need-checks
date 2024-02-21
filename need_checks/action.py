from __future__ import annotations

from base64 import b64decode
from enum import Enum
from time import sleep
from typing import cast

import click
import strictyaml as yaml
from fastcore.net import HTTP404NotFoundError
from ghapi.all import GhApi

from . import errors, ui
from .context import Context
from .types import CheckRun, CheckRunList, GitRef, Job, WorkflowRun


class Conclusion(Enum):
    OK = "OK"
    KO = "KO"
    WAIT = "WAIT"


def get_ref(github: GhApi, owner: str, repo: str, label: str) -> GitRef:
    label = label.removeprefix("refs/")
    for ref in label, f"tags/{label}", f"heads/{label}":
        try:
            return cast(GitRef, github.git.get_ref(owner=owner, repo=repo, ref=ref))
        except HTTP404NotFoundError:
            continue
    raise errors.UnknownRef(f"Ref {label} is unknown")


def get_current_job(github: GhApi, ctx: Context) -> Job:
    jobs = github.actions.list_jobs_for_workflow_run(
        owner=ctx.github.repository_owner,
        repo=ctx.github.event.repository.name,
        run_id=ctx.github.run_id,
    )
    for job in jobs["jobs"]:
        if job["name"] == ctx.github.job:
            return job
    # Job not found by job-id, it must have a name
    workflow = fetch_workflow(github, ctx.github.workflow_ref)
    if (jobdef := workflow.get("jobs", {}).get(ctx.github.job)) is not None:
        job_name = jobdef["name"]
        for job in jobs["jobs"]:
            if job["name"] == job_name:
                return job

    raise errors.JobNotFound(f"Unable to find current job {ctx.github.job}")


def fetch_workflow(github: GhApi, workflow_ref: str) -> dict:
    repo_path, ref = workflow_ref.split("@")
    owner, repo, path = repo_path.split("/", 2)
    content = github.repos.get_content(
        owner=owner,
        repo=repo,
        path=path,
        ref=ref.removeprefix("refs/"),
    )
    decoded = b64decode(content.content).decode("utf8")
    return yaml.load(decoded)


def select_checks(
    github: GhApi,
    ctx: Context,
    gitref: GitRef,
    current_job: Job,
    check_suite: int | None = None,
    include: str | list[str] | None = None,
    exclude: str | list[str] | None = None,
) -> list[CheckRun]:
    checks = (
        cast(
            CheckRunList,
            github.checks.list_for_ref(
                owner=ctx.inputs.target_owner, repo=ctx.inputs.target_repo, ref=gitref["ref"]
            ),
        ).get("check_runs")
        or []
    )
    filtered = (check for check in checks if check["name"] != current_job["name"])
    if check_suite:
        filtered = (
            check
            for check in filtered
            if (check.get("check_suite") or {}).get("id") == check_suite  # type: ignore[call-overload]
        )  # type: ignore[call-overload]
    return list(filtered)


def decide_for_checks(ctx: Context, checks: list[CheckRun]) -> Conclusion:
    if not checks:
        return Conclusion.OK

    completed = [check for check in checks if check["status"] == "completed"]
    remaining = [check for check in checks if check["status"] != "completed"]

    if any(check["conclusion"] not in ctx.inputs.conclusions for check in completed):
        return Conclusion.KO
    elif remaining:
        return Conclusion.WAIT if ctx.inputs.wait else Conclusion.KO
    else:
        return Conclusion.OK


def run(ctx: Context):
    ui.display_inputs("Inputs", ctx)

    github = GhApi(token=ctx.inputs.token)
    ref = get_ref(github, ctx.inputs.target_owner, ctx.inputs.target_repo, ctx.inputs.ref)
    print(f"🔖 {ui.bold('Current ref')}: {ui.ref_type(ref)}")

    job = get_current_job(github, ctx)
    print(f"💼 {ui.bold('Current job')}: {job['name']} (#{job['id']})")

    check_suite: int | None = None
    if ctx.inputs.workflow:
        runs = github.actions.list_workflow_runs(
            owner=ctx.inputs.target_owner,
            repo=ctx.inputs.target_repo,
            workflow_id=ctx.inputs.workflow,
            head_sha=ref["object"]["sha"],
        )
        if not runs.workflow_runs:
            raise errors.RequirementsNotMet("The workflow was not run on the commit")
        last_run = cast(WorkflowRun, runs.workflow_runs[-1])
        check_suite = last_run["check_suite_id"]

    waited_for = 0
    while True:
        checks = select_checks(github, ctx, ref, job, check_suite=check_suite)
        ui.display_checks("Found checks", checks)
        match decide_for_checks(ctx, checks):
            case Conclusion.OK:
                print("✅ All checks met the requirements")
                break
            case Conclusion.KO:
                raise errors.RequirementsNotMet("Some checks don't meet the requirements")
            case Conclusion.WAIT:
                if ctx.inputs.wait_timeout and waited_for >= ctx.inputs.wait_timeout:
                    raise errors.Timeout(f"Timeout reached after waiting for {waited_for}s")
                print(f"⏳ Waiting for {ctx.inputs.wait_interval} seconds")
                waited_for += ctx.inputs.wait_interval
                sleep(ctx.inputs.wait_interval)


@click.command
def __main__():
    ctx = Context()
    try:
        run(ctx)
    except errors.ActionError as error:
        print(f"❌ {error}")
        exit(-1)
