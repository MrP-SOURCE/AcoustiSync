from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_streamlit_app_starts_without_exceptions():
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    assert not app.exception
    assert app.title[0].value == "AcoustiSync"
    assert app.radio[0].options == ["HOME AUDIO", "CAR AUDIO"]


def test_home_placement_calculation_and_3d_plot_run():
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    app.button[0].click().run()
    assert not app.exception


def test_car_enclosure_calculation_runs():
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    app.radio[0].set_value("CAR AUDIO").run()
    app.button[0].click().run()
    assert not app.exception


def test_car_component_placement_runs():
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    app.radio[0].set_value("CAR AUDIO").run()
    app.radio[1].set_value("Component speaker placement").run()
    app.button[0].click().run()
    assert not app.exception


def test_home_diy_high_qts_is_handled_without_app_crash():
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    app.radio[1].set_value("Driver-in-hand / DIY enclosure").run()
    qts_input = next(item for item in app.number_input if item.label == "Qts")
    qts_input.set_value(0.9)
    design_button = next(item for item in app.button if item.label == "Design enclosure")
    design_button.click().run()
    assert not app.exception
    assert any("Qtc 0.707" in warning.value for warning in app.warning)
