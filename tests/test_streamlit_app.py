"""Tests for the Streamlit application."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app" / "main.py"


def test_streamlit_dashboard_loads_without_errors() -> None:
    """The application should render without raising an exception."""

    app = AppTest.from_file(
        APP_PATH,
        default_timeout=15,
    )

    app.run()

    assert not app.exception
    assert app.title[0].value == "🌿 Plant Health Platform"
    assert len(app.metric) == 4