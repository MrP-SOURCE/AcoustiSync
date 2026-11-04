from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_app_starts_without_exceptions():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=15).run()
    assert not app.exception
    assert app.title[0].value == "AcoustiSync"
    assert app.radio[0].options == ["HOME AUDIO", "CAR AUDIO"]
