from __future__ import annotations

from typing import Literal, NotRequired, TypedDict


class Node(TypedDict):
    id: int
    node_id: str


class Timestamped(TypedDict):
    created_at: str
    updated_at: str


class GitRefObject(TypedDict):
    sha: str
    type: str
    url: str


class GitRef(TypedDict):
    ref: str
    node_id: str
    url: str
    object: GitRefObject


class CheckRunOutput(TypedDict):
    title: str | None
    summary: str | None
    text: str | None
    annotations_count: int
    annotations_url: str


class WrappedId(TypedDict):
    id: int


class Person(TypedDict):
    name: str
    email: str


class User(Node):
    name: str | None
    email: str | None
    login: str
    avatar_url: str
    gravatar_id: str | None
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    site_admin: bool
    starred_at: NotRequired[str]


class Permissions(TypedDict, total=False):
    issues: str
    checks: str
    metadata: str
    contents: str
    deployments: str
    admin: str
    maintain: str
    push: str
    triage: str
    pull: str


class App(Node, Timestamped):
    name: str
    slug: NotRequired[str]
    owner: User | None
    description: str | None
    external_url: str
    html_url: str
    permissions: Permissions
    events: list[str]
    installations_count: NotRequired[int]
    client_id: NotRequired[str]
    client_secret: NotRequired[str]
    webhook_secret: NotRequired[str | None]
    pem: NotRequired[str]


class Repo(TypedDict):
    id: int
    url: str
    name: str


class Head(TypedDict):
    ref: str
    sha: str
    repo: Repo


class PullRequest(TypedDict):
    id: int
    number: int
    url: str
    head: Head
    base: Head


class Deployment(Node, Timestamped):
    url: str
    task: str
    original_environment: NotRequired[str]
    environment: str
    description: str | None
    statuses_url: str
    repository_url: str
    transient_environment: NotRequired[bool]
    production_environment: NotRequired[bool]
    performed_via_github_app: NotRequired[App | None]


class CheckRun(Node):
    name: str
    head_sha: str
    external_id: str | None
    url: str
    html_url: str | None
    details_url: str | None
    status: Literal["queued", "in_progress", "completed"]
    conclusion: Literal[
        "success",
        "failure",
        "neutral",
        "cancelled",
        "skipped",
        "timed_out",
        "action_required",
    ] | None
    started_at: str | None
    completed_at: str | None
    output: CheckRunOutput
    check_suite: WrappedId | None
    app: App | None
    pull_request: list[PullRequest]
    deployment: NotRequired[Deployment]


class ResultList(TypedDict):
    total_count: int


class CheckRunList(ResultList):
    check_runs: list[CheckRun]


class ReferencedWorkflow(TypedDict):
    path: str
    sha: str
    ref: NotRequired[str]


class Commit(TypedDict):
    id: str
    tree_id: str
    message: str
    timestamp: str
    author: Person | None
    committer: Person | None


class CodeOfConduct(TypedDict):
    name: str
    url: str
    body: str
    html_url: str | None


class License(TypedDict, total=False):
    key: str
    name: str
    spdx_id: str
    url: str
    node_id: str


class ToggledStatus(TypedDict):
    status: Literal["enabled", "disabled"]


class SecurityAndAnalysis(TypedDict):
    advanced_security: ToggledStatus
    dependabot_security_updates: ToggledStatus
    secret_scanning: ToggledStatus
    secret_scanning_push_protection: ToggledStatus


class MinimalRepository(Node, Timestamped):
    name: str
    full_name: str
    owner: User
    private: bool
    html_url: str
    description: str | None
    fork: bool
    url: str
    archive_url: str
    assignees_url: str
    blobs_url: str
    branches_url: str
    collaborators_url: str
    comments_url: str
    commits_url: str
    compare_url: str
    contents_url: str
    contributors_url: str
    deployments_url: str
    downloads_url: str
    events_url: str
    forks_url: str
    git_commits_url: str
    git_tags_url: str
    git_refs_url: str
    git_url: NotRequired[str]
    issue_comment_url: str
    issue_events_url: str
    issues_url: str
    keys_url: str
    labels_url: str
    languages_url: str
    merges_url: str
    milestones_url: str
    notifications_url: str
    pulls_url: str
    releases_url: str
    ssh_url: str
    stargazers_url: str
    statuses_url: str
    subscribers_url: str
    subscription_url: str
    tags_url: str
    teams_url: str
    trees_url: str
    clone_url: NotRequired[str]
    mirror_url: NotRequired[str]
    hooks_url: str
    svn_url: NotRequired[str]
    homepage: NotRequired[str | None]
    language: NotRequired[str | None]
    forks_count: NotRequired[int]
    stargazers_count: NotRequired[int]
    watchers_count: NotRequired[int]
    size: NotRequired[int]
    default_branch: NotRequired[str]
    open_issues_count: NotRequired[int]
    is_template: NotRequired[bool]
    topics: NotRequired[list[str]]
    has_issues: NotRequired[bool]
    has_projects: NotRequired[bool]
    has_wiki: NotRequired[bool]
    has_downloads: NotRequired[bool]
    has_discussions: NotRequired[bool]
    archived: NotRequired[bool]
    disabled: NotRequired[bool]
    visibility: NotRequired[str]
    pushed_at: NotRequired[str | None]
    permissions: NotRequired[Permissions]
    role_name: NotRequired[str]
    temp_clone_token: NotRequired[str]
    delete_branch_on_merge: NotRequired[bool]
    subscribers_count: NotRequired[int]
    network_count: NotRequired[int]
    code_of_conduct: NotRequired[CodeOfConduct]
    license: NotRequired[License | None]
    forks: NotRequired[int]
    open_issues: NotRequired[int]
    watchers: NotRequired[int]
    allow_forking: NotRequired[bool]
    web_commit_signoff_required: NotRequired[bool]
    security_and_analysis: NotRequired[SecurityAndAnalysis]


class WorkflowRun(Node, Timestamped):
    name: NotRequired[str | None]
    check_suite_id: NotRequired[int]
    check_suite_node_id: NotRequired[str]
    head_branch: str | None
    head_sha: str
    path: str
    run_number: int
    run_attempt: NotRequired[int]
    referenced_workflows: NotRequired[list[ReferencedWorkflow] | None]
    event: str
    status: str | None
    conclusion: str | None
    workflow_id: int
    url: str
    html_url: str
    pull_requests: NotRequired[list[PullRequest] | None]
    actor: NotRequired[User]
    triggering_actor: NotRequired[User]
    run_started_at: NotRequired[str]
    jobs_url: str
    logs_url: str
    check_suite_url: str
    artifacts_url: str
    cancel_url: str
    rerun_url: str
    previous_attempt_url: NotRequired[str | None]
    workflow_url: str
    head_commit: Commit | None
    repository: MinimalRepository
    head_repository: MinimalRepository
    head_repository_id: NotRequired[int]
    display_title: str


class WorkflowRunList(ResultList):
    workflow_runs: list[WorkflowRun]


type Conclusion = Literal[  # type: ignore[valid-type]
    "success",
    "failure",
    "neutral",
    "cancelled",
    "skipped",
    "timed_out",
    "action_required",
    "startup_failure",
    "stale",
]

type Status = Literal["queued", "in_progress", "completed"]  # type: ignore[valid-type]

type JobStatus = Status | Literal["waiting"]  # type: ignore[valid-type]


class CheckSuite(Node, Timestamped):
    head_branch: str | None
    head_sha: str | None
    status: Status | None
    conclusion: Conclusion | None
    url: str | None
    before: str | None
    after: str | None
    pull_requests: list[PullRequest] | None
    app: App | None
    repository: MinimalRepository
    head_commit: Commit
    last_check_runs_count: int
    check_runs_url: str
    rerequestable: NotRequired[bool]
    runs_rerequestable: NotRequired[bool]


class Step(TypedDict):
    status: Status
    conclusion: str | None
    name: str
    number: int
    started_at: str | None
    completed_at: str | None


class Job(Node):
    run_id: int
    run_url: str
    run_attempt: NotRequired[int]
    head_sha: str
    url: str
    html_url: str | None
    status: JobStatus
    conclusion: Conclusion | None
    created_at: str
    started_at: str
    completed_at: str | None
    name: str
    steps: NotRequired[list[Step]]
    check_run_url: str
    labels: list[str]
    runner_id: int | None
    runner_name: str | None
    runner_group_id: int | None
    runner_group_name: str | None
    workflow_name: str | None
    head_branch: str | None


class JobList(ResultList):
    jobs: list[Job]


class ContentLinks:
    git: str | None
    html: str | None
    self: str | None


class Content(TypedDict):
    type: str
    size: int
    name: str
    path: str
    sha: str
    url: str
    git_url: str
    html_url: str
    download_url: str
    entries: NotRequired[list[Content]]
    _links: ContentLinks
    content: str
    encoding: str
