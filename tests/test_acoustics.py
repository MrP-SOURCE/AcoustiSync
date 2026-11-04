import math

import pytest

from acoustics import (
    estimate_ported_box,
    estimate_sealed_box,
    lookup_driver,
    port_length_cm,
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
