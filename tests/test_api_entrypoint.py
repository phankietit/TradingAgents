"""CLI admission must not read credentials or start a server for help/errors."""
import pytest

from tradingagents.platform.api import runtime


def forbid_startup(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Help/error admitted configuration or service startup")
    monkeypatch.setattr(runtime, "load_api_settings", forbidden)
    monkeypatch.setattr(runtime, "configure_platform_logging", forbidden)
    monkeypatch.setattr(runtime, "create_app", forbidden)
    monkeypatch.setattr(runtime.uvicorn, "run", forbidden)


def test_api_help_exits_without_configuration_or_service(monkeypatch, capsys):
    forbid_startup(monkeypatch)
    with pytest.raises(SystemExit) as stopped:
        runtime.main(["--help"])
    assert stopped.value.code == 0
    output = capsys.readouterr()
    assert "tradingagents-api" in output.out
    assert "TRADINGAGENTS_DATABASE_URL" in output.out
    assert not output.err


def test_unknown_api_arguments_refuse_before_startup_and_do_not_echo_values(monkeypatch, capsys):
    forbid_startup(monkeypatch)
    private_marker = "synthetic-private-input-marker"
    with pytest.raises(SystemExit) as stopped:
        runtime.main(["--unknown-option", private_marker])
    assert stopped.value.code == 2
    output = capsys.readouterr()
    assert "unrecognized command-line options" in output.err
    assert private_marker not in output.out + output.err
