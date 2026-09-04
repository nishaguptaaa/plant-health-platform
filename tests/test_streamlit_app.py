"""Tests for the Streamlit application shell."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app" / "main.py"


def test_streamlit_dashboard_loads_without_errors() -> None:
    """The dashboard should render even when its database is empty."""

    app = AppTest.from_file(APP_PATH)
    app.run()

    assert not app.exception
    assert app.title[0].value == "🌿 Plant Health Platform"
    assert len(app.metric) == 4
    assert app.metric[0].label == "Plants"
    assert app.metric[1].label == "Open tasks"
    assert app.metric[2].label == "Active health issues"
    assert app.metric[3].label == "Weather snapshots"