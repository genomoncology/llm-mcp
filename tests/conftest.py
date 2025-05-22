from pytest import fixture


@fixture(scope="module")
def vcr_config():
    """Ensure tokens are not stored to GitHub."""
    return {"filter_headers": ["authorization"]}
