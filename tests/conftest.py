from pathlib import Path

from pytest import fixture


@fixture(scope="module")
def vcr_config():
    """Ensure tokens are not stored to GitHub."""
    return {"filter_headers": ["authorization"]}


@fixture(scope="session")
def data_dir() -> Path:
    return Path(__file__).parent / "data"
