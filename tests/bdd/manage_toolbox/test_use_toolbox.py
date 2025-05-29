import pytest
from pytest_bdd import scenarios

scenarios("./manage_toolbox/use_toolbox.feature")
pytestmark = pytest.mark.vcr(record_mode="new_episodes")
