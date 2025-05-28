from pathlib import Path

from pytest_bdd import then


@then("the output should contain the secret text exactly as written")
def output_should_contain_secret_text(cli_result, data_dir: Path):
    """Assert the CLI output includes the contents of *tests/data/secret.txt*."""
    secret = (data_dir / "secret.txt").read_text().strip().strip('"')
    assert secret in cli_result.output
