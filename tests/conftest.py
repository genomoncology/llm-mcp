from pathlib import Path

import pytest

pytestmark = pytest.mark.vcr(record_mode="new_episodes")


@pytest.fixture(scope="module")
def vcr_config():
    """Ensure tokens are not stored to GitHub."""
    return {"filter_headers": ["authorization"]}


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return Path(__file__).parent / "data"
