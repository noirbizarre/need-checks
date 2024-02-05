from __future__ import annotations

from polyfactory.factories.typed_dict_factory import TypedDictFactory

from need_checks import types


class GitRefObjectFactory(TypedDictFactory[types.GitRefObject]):
    @classmethod
    def sha(cls) -> str:
        return cls.__faker__.sha1()

    @classmethod
    def type(cls) -> str:
        return cls.__random__.choice(["commit"])


class GitRefFactory(TypedDictFactory[types.GitRef]):
    object = GitRefObjectFactory


class AppFactory(TypedDictFactory[types.App]):
    pass


class CheckRunFactory(TypedDictFactory[types.CheckRun]):
    @classmethod
    def head_sha(cls) -> str:
        return cls.__faker__.sha1()


class JobFactory(TypedDictFactory[types.Job]):
    pass


class ContentFactory(TypedDictFactory[types.Content]):
    encoding = "base64"


class WorkflowRunFactory(TypedDictFactory[types.WorkflowRun]):
    pass
