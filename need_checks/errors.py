from __future__ import annotations


class ActionError(Exception):
    pass


class UnknownRef(ActionError):
    pass


class JobNotFound(ActionError):
    pass


class RequirementsNotMet(ActionError):
    pass


class Timeout(ActionError):
    pass
