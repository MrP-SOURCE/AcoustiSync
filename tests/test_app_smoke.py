from pathlib import Path

import pytest
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


@pytest.mark.parametrize("sub_count", [0, 1, 2, 4])
def test_home_subwoofer_screening_options_render(sub_count):
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    selector = next(
        item for item in app.selectbox
        if item.label == "Number of subwoofers to screen"
    )
    selector.set_value(sub_count).run()
    calculate = next(
        item for item in app.button
        if item.label == "Calculate placement plan"
    )
    calculate.click().run()

    assert not app.exception
    screening_text = [
        item.value for item in app.markdown
        if "Subwoofer placement screening" in item.value
    ]
    assert bool(screening_text) is (sub_count > 0)
    coordinate_tables = [
        item.value for item in app.dataframe
        if hasattr(item.value, "columns")
        and "Distance from left wall" in item.value.columns
    ]
    if sub_count == 0:
        assert not coordinate_tables
    else:
        assert len(coordinate_tables) == 1
        assert len(coordinate_tables[0]) == sub_count
        assert list(coordinate_tables[0]["Subwoofer"]) == [
            f"SUB {index}" for index in range(1, sub_count + 1)
        ]
        coordinates = coordinate_tables[0]
        x_positions = [float(value.split()[0]) for value in coordinates["Distance from left wall"]]
        y_positions = [float(value.split()[0]) for value in coordinates["Distance from front wall"]]
        assert all(0.0 < x < 3.8 for x in x_positions)
        assert all(0.0 < y < 5.0 for y in y_positions)
        if sub_count == 1:
            assert (x_positions[0], y_positions[0]) == pytest.approx((1.9, 0.45))
        elif sub_count == 2:
            assert x_positions == pytest.approx([1.9, 1.9])
            assert y_positions == pytest.approx([0.45, 4.55])
        else:
            assert x_positions == pytest.approx([1.9, 1.9, 0.6, 3.2])
            assert y_positions == pytest.approx([0.45, 4.55, 2.5, 2.5])


@pytest.mark.parametrize(
    "sub_count, expected_x, expected_y",
    [
        (1, [1.0], [0.4]),
        (2, [1.0, 1.0], [0.4, 1.6]),
        (4, [1.0, 1.0, 0.4, 1.6], [0.4, 1.6, 1.0, 1.0]),
    ],
)
def test_subwoofer_positions_stay_inside_minimum_room_at_maximum_clearances(
    sub_count, expected_x, expected_y
):
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    values = {
        "Room length (m)": 2.0,
        "Room width (m)": 2.0,
        "Available speaker distance from front wall (m)": 2.0,
        "Available distance from side wall (m)": 2.0,
    }
    for label, value in values.items():
        next(item for item in app.number_input if item.label == label).set_value(value)
    next(
        item for item in app.selectbox
        if item.label == "Number of subwoofers to screen"
    ).set_value(sub_count)
    app.run()

    calculate = next(
        item for item in app.button
        if item.label == "Calculate placement plan"
    )
    calculate.click().run()

    assert not app.exception
    coordinates = next(
        item.value for item in app.dataframe
        if hasattr(item.value, "columns")
        and "Distance from left wall" in item.value.columns
    )
    x_positions = [
        float(value.split()[0])
        for value in coordinates["Distance from left wall"]
    ]
    y_positions = [
        float(value.split()[0])
        for value in coordinates["Distance from front wall"]
    ]
    assert all(0.0 < x < 2.0 for x in x_positions)
    assert all(0.0 < y < 2.0 for y in y_positions)
    assert x_positions == pytest.approx(expected_x)
    assert y_positions == pytest.approx(expected_y)


def test_car_enclosure_calculation_runs():
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    app.radio[0].set_value("CAR AUDIO").run()
    app.button[0].click().run()
    assert not app.exception
    rendered = "\\n".join(item.value for item in app.markdown)
    assert "Estimated usable box space" in rendered
    assert "Port tube starting size" in rendered
    assert "Available rectangular envelope" in rendered
    assert "Suggested box size" in rendered
    assert (
        "exceeds at least one entered vehicle dimension" in rendered
        or "fits the entered rectangular envelope" in rendered
    )


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


def test_home_diy_enclosure_renders_volume_and_port_outputs():
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    app.radio[1].set_value("Driver-in-hand / DIY enclosure").run()
    next(item for item in app.button if item.label == "Design enclosure").click().run()
    assert not app.exception
    rendered = "\\n".join(item.value for item in app.markdown)
    assert "Port tube starting size" in rendered
    assert "estimated gross internal volume" in rendered
    assert "port displacement" in rendered
    assert "Suggested internal enclosure size" in rendered
    assert "Basic six-panel cut list" in rendered
