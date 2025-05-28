import pytest
from pytest_bdd import scenarios

scenarios("./manage_toolbox/validate_toolbox.feature")
pytestmark = pytest.mark.vcr(record_mode="new_episodes")
