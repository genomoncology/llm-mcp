import pytest
from pytest_bdd import scenarios

scenarios("./manage_toolbox/remove_toolbox.feature")
pytestmark = pytest.mark.vcr(record_mode="new_episodes")
