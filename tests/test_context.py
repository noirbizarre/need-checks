from need_checks.context import Inputs


def test_conclusions_as_list():
    inputs = Inputs(conclusions=["success", "skipped", "cancelled"])

    assert inputs.conclusions == ["success", "skipped", "cancelled"]


def test_parse_comma_separated_conclusions():
    inputs = Inputs(conclusions="success,skipped, cancelled")

    assert inputs.conclusions == ["success", "skipped", "cancelled"]


def test_target_owner_and_repo():
    inputs = Inputs(repository="owner/repo")

    assert inputs.target_owner == "owner"
    assert inputs.target_repo == "repo"
