import pytest
from pytest_bdd import scenarios

scenarios("./use_tools/use_remote_tools.feature")
pytestmark = pytest.mark.vcr()
