import pytest
from pytest_bdd import scenarios

scenarios("./manage_toolbox/add_mcp_tools.feature")
pytestmark = pytest.mark.vcr(record_mode="new_episodes")
