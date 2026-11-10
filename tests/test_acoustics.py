import math

import pytest

from acoustics import (
    estimate_ported_box,
    estimate_sealed_box,
    gross_enclosure_volume_l,
    rectangular_enclosure_dimensions,
    lookup_driver,
    port_length_cm,
    round_port_end_clearance_cm,
    placement_guidance,
    room_axial_modes,
    sabine_rt60,
    wavelength,
)


def test_wavelength_80_hz():
    assert wavelength(80) == pytest.approx(343 / 80)


def test_wavelength_rejects_nonpositive_frequency():
    with pytest.raises(ValueError):
        wavelength(0)


def test_room_modes_returns_three_axes_and_sorted_frequencies():
    modes = room_axial_modes(5.0, 4.0, 2.5)
    assert len(modes) == 12
    assert [item[2] for item in modes] == sorted(item[2] for item in modes)
    assert {item[0] for item in modes} == {"Length", "Width", "Height"}


def test_room_modes_rejects_invalid_dimensions():
    with pytest.raises(ValueError):
        room_axial_modes(5.0, 0.0, 2.5)


def test_sealed_box_estimate_is_positive_and_hits_target_qtc():
    result = estimate_sealed_box(30.0, 0.42, 55.0)
    assert result["vb_l"] > 0
    assert result["fc_hz"] > 30
    assert result["qtc"] == pytest.approx(0.707)


def test_ported_box_screening_estimate_is_positive():
    result = estimate_ported_box(30.0, 0.42, 55.0)
    assert result["vb_l"] > 0
    assert result["fb_hz"] > 0


@pytest.mark.parametrize(
    "fs_hz, qts, vas_l",
    [(0, 0.42, 55.0), (30.0, 0, 55.0), (30.0, 0.42, 0)],
)
def test_ported_box_rejects_nonpositive_driver_inputs(fs_hz, qts, vas_l):
    with pytest.raises(ValueError):
        estimate_ported_box(fs_hz, qts, vas_l)


def test_port_length_is_nonnegative():
    assert port_length_cm(78.54, 40.0, 32.0) >= 0


def test_port_length_matches_diameter_based_round_port_formula():
    area_cm2 = math.pi * (10.0 / 2.0) ** 2
    expected = (23562.5 * 10.0**2 / (32.0**2 * 40.0)) - (0.732 * 10.0)
    assert port_length_cm(area_cm2, 40.0, 32.0) == pytest.approx(expected)


def test_port_length_rejects_nonpositive_inputs():
    with pytest.raises(ValueError):
        port_length_cm(0, 40.0, 32.0)


def test_demo_driver_is_explicitly_unverified():
    result = lookup_driver("Mission Subwoofer Driver")
    assert result["found"] is True
    assert "unverified" in result["model"].lower()


def test_unknown_driver_is_not_marked_found():
    result = lookup_driver("Not a real driver")
    assert result["found"] is False


def test_placement_guidance_mentions_measurement():
    result = placement_guidance(0.4, 0.5, 2.5, False, "Music")
    assert "Measure bass response" in result


def test_sabine_rt60_uses_volume_and_absorption_area():
    assert sabine_rt60(50.0, 10.0) == pytest.approx(0.805)


@pytest.mark.parametrize("volume, absorption", [(0, 10), (10, 0), (-1, 2), (2, -1)])
def test_sabine_rt60_rejects_nonpositive_inputs(volume, absorption):
    with pytest.raises(ValueError):
        sabine_rt60(volume, absorption)


def test_gross_enclosure_volume_includes_driver_bracing_and_port():
    result = gross_enclosure_volume_l(40.0, 1.2, 0.8, 78.54, 20.0)
    assert result["port_displacement_l"] == pytest.approx(1.5708)
    assert result["gross_volume_l"] == pytest.approx(43.5708)


@pytest.mark.parametrize(
    "values",
    [
        (0, 1, 1, 10, 10),
        (10, -1, 1, 10, 10),
        (10, 1, -1, 10, 10),
        (10, 1, 1, -10, 10),
        (10, 1, 1, 10, -10),
    ],
)
def test_gross_enclosure_volume_rejects_invalid_inputs(values):
    with pytest.raises(ValueError):
        gross_enclosure_volume_l(*values)


@pytest.mark.parametrize(
    "values",
    [
        (float("nan"), 40.0, 32.0, 0.732),
        (78.54, float("inf"), 32.0, 0.732),
        (78.54, 40.0, 32.0, float("nan")),
        (78.54, 40.0, 32.0, -0.1),
    ],
)
def test_port_length_rejects_nonfinite_or_negative_end_correction(values):
    with pytest.raises(ValueError):
        port_length_cm(*values)


@pytest.mark.parametrize(
    "values",
    [
        (float("nan"), 1, 1, 1, 1),
        (10, float("inf"), 1, 1, 1),
    ],
)
def test_gross_enclosure_volume_rejects_nonfinite_inputs(values):
    with pytest.raises(ValueError):
        gross_enclosure_volume_l(*values)


def test_rectangular_enclosure_dimensions_match_target_volume_and_panel_thickness():
    result = rectangular_enclosure_dimensions(60.0, 18.0)
    internal_volume = (
        result["internal_width_cm"]
        * result["internal_height_cm"]
        * result["internal_depth_cm"]
        / 1000
    )
    assert internal_volume == pytest.approx(60.0)
    assert result["external_width_cm"] - result["internal_width_cm"] == pytest.approx(3.6)
    assert result["front_back_panels"][2] == 2
    assert result["top_bottom_panels"][2] == 2
    assert result["side_panels"][2] == 2


@pytest.mark.parametrize("values", [(0, 18, 1.5, 1), (40, 0, 1.5, 1), (40, 18, 0, 1)])
def test_rectangular_enclosure_dimensions_reject_invalid_inputs(values):
    with pytest.raises(ValueError):
        rectangular_enclosure_dimensions(*values)


@pytest.mark.parametrize(
    "depth, length, expected",
    [(40.0, 20.0, 20.0), (30.0, 30.0, 0.0), (25.0, 32.0, -7.0)],
)
def test_round_port_end_clearance(depth, length, expected):
    assert round_port_end_clearance_cm(depth, length) == pytest.approx(expected)


@pytest.mark.parametrize("values", [(0, 1), (1, -1), (float("nan"), 1)])
def test_round_port_end_clearance_rejects_invalid_inputs(values):
    with pytest.raises(ValueError):
        round_port_end_clearance_cm(*values)


@pytest.mark.parametrize("frequency, speed", [
    (float("nan"), 343.0),
    (80.0, float("inf")),
    (0.0, 343.0),
    (80.0, 0.0),
])
def test_wavelength_rejects_nonfinite_or_nonpositive_inputs(frequency, speed):
    with pytest.raises(ValueError):
        wavelength(frequency, speed)


@pytest.mark.parametrize(
    "dimensions, max_order",
    [
        ((float("nan"), 4.0, 2.5), 4),
        ((5.0, float("inf"), 2.5), 4),
        ((5.0, 4.0, 2.5), 0),
        ((5.0, 4.0, 2.5), 1.5),
    ],
)
def test_room_modes_rejects_nonfinite_dimensions_or_invalid_order(dimensions, max_order):
    with pytest.raises(ValueError):
        room_axial_modes(*dimensions, max_order=max_order)


@pytest.mark.parametrize("volume, absorption", [
    (float("nan"), 10.0),
    (10.0, float("inf")),
])
def test_sabine_rt60_rejects_nonfinite_inputs(volume, absorption):
    with pytest.raises(ValueError):
        sabine_rt60(volume, absorption)


@pytest.mark.parametrize(
    "values",
    [
        (float("nan"), 0.42, 55.0, 0.707),
        (30.0, float("inf"), 55.0, 0.707),
        (30.0, 0.42, float("nan"), 0.707),
        (30.0, 0.42, 55.0, float("inf")),
    ],
)
def test_sealed_box_rejects_nonfinite_inputs(values):
    with pytest.raises(ValueError):
        estimate_sealed_box(*values)


@pytest.mark.parametrize(
    "values",
    [
        (float("nan"), 0.42, 55.0),
        (30.0, float("inf"), 55.0),
        (30.0, 0.42, float("nan")),
    ],
)
def test_ported_box_rejects_nonfinite_inputs(values):
    with pytest.raises(ValueError):
        estimate_ported_box(*values)


@pytest.mark.parametrize(
    "values",
    [
        (float("nan"), 12.0, 35.0, 50.0),
        (500.0, float("inf"), 35.0, 50.0),
        (500.0, 12.0, float("nan"), 50.0),
        (500.0, 12.0, 35.0, float("inf")),
        (0.0, 12.0, 35.0, 50.0),
    ],
)
def test_port_velocity_rejects_nonfinite_or_nonpositive_inputs(values):
    from acoustics import port_velocity

    with pytest.raises(ValueError):
        port_velocity(*values)


def test_port_velocity_returns_positive_speed_for_valid_inputs():
    from acoustics import port_velocity

    assert port_velocity(500.0, 12.0, 35.0, 50.0) > 0
