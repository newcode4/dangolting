import inspect

from utils import streamlit_cleanup


def test_cleanup_disconnects_stale_observers():
    src = inspect.getsource(streamlit_cleanup.cleanup_stale_streamlit_shell)
    assert "dgt-shell-hide" in src
    assert "__dgtShellObserver" in src
    assert "disconnect" in src


def test_app_runs_cleanup_on_public_gate():
    app = open("app.py", encoding="utf-8").read()
    gate = app[app.find("def _public_entry_gate"): app.find("_public_entry_gate(logo_data_uri())")]
    assert "cleanup_stale_streamlit_shell()" in gate
