import os
from pathlib import Path

import llm
import pytest

pytestmark = pytest.mark.vcr(record_mode="new_episodes")


@pytest.fixture(scope="module")
def vcr_config():
    """Ensure tokens are not stored to GitHub."""
    return {"filter_headers": ["authorization"]}


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def llm_user_dir(tmp_path_factory):
    llm_user_dir = tmp_path_factory.mktemp("llm_user_dir")
    llm_user_dir.mkdir(parents=True, exist_ok=True)
    os.environ["LLM_USER_PATH"] = str(llm_user_dir)
    assert llm.user_dir() == llm_user_dir, "Failed to set LLM_USER_PATH"
    return llm_user_dir
