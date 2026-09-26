import pytest
from click.testing import CliRunner

from delivery_copilot.cli import cli


@pytest.fixture
def temp_store(tmp_path, monkeypatch):
    data_file = tmp_path / "engagements.json"
    data_file.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("DELIVERY_COPILOT_DATA", str(data_file))
    return data_file


def test_engagement_add_and_list(temp_store):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["engagement", "add", "--client", "Acme", "--name", "Revamp", "--lead", "lead@valtech.com"],
    )
    assert result.exit_code == 0
    assert "Created engagement" in result.output

    result = runner.invoke(cli, ["engagement", "list"])
    assert result.exit_code == 0
    assert "Acme" in result.output


def test_risk_add_requires_valid_engagement(temp_store):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["risk", "add", "eng-nope", "--description", "x", "--severity", "high", "--owner", "a@valtech.com"],
    )
    assert result.exit_code != 0
    assert "No engagement found" in result.output


def test_full_flow(temp_store):
    runner = CliRunner()
    add_result = runner.invoke(
        cli,
        ["engagement", "add", "--client", "Acme", "--name", "Revamp", "--lead", "lead@valtech.com"],
    )
    engagement_id = add_result.output.split()[-1]

    result = runner.invoke(
        cli,
        ["risk", "add", engagement_id, "--description", "Vendor delay", "--severity", "high", "--owner", "lead@valtech.com"],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        cli,
        ["time", "log", engagement_id, "--consultant", "dev@valtech.com", "--hours", "3"],
    )
    assert result.exit_code == 0

    result = runner.invoke(cli, ["report", "status", engagement_id])
    assert result.exit_code == 0
    assert "Vendor delay" in result.output
