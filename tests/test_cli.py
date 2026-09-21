import json

from quant_research.cli import main


def test_cli_writes_reproducible_artifact(tmp_path) -> None:
    one = tmp_path / "one.json"
    two = tmp_path / "two.json"
    assert main(["--seed", "42", "--periods", "30", "--output", str(one)]) == 0
    assert main(["--seed", "42", "--periods", "30", "--output", str(two)]) == 0
    assert one.read_bytes() == two.read_bytes()
    payload = json.loads(one.read_text())
    assert payload["assumptions"].startswith("close signal")
    assert payload["metrics"]["final_equity"]
