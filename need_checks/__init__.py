from importlib.resources import files


def read_version() -> str:
    version_file = files(__package__) / "VERSION"
    return version_file.read_text() if version_file.is_file() else "0.0.0.dev"


__version__ = read_version()
