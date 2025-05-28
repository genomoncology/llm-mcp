import pytest
from pytest_bdd import scenarios

scenarios("./use_tools/use_local_tools.feature")
pytestmark = pytest.mark.vcr()
