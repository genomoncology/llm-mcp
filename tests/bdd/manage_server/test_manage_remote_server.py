import pytest
from pytest_bdd import scenarios

scenarios("./manage_server/manage_remote_server.feature")
pytestmark = pytest.mark.vcr()
