"""Acoustic helper functions for AcoustiSync. SI units unless stated otherwise."""
import math

SPEED_OF_SOUND = 343.0

# Clearly marked sample records only. Replace with verified, licensed data sources.
DEMO_DRIVERS = {
    "demo 12 inch": {"model":"Demo 12-inch (illustrative)", "Fs":28.0, "Qts":0.42, "Vas":55.0, "Re":3.6, "Xmax":12.0, "found":True},
    "mission subwoofer driver": {"model":"Mission Subwoofer Driver (unverified demo)", "Fs":30.0, "Qts":0.48, "Vas":42.0, "Re":3.4, "Xmax":7.0, "found":True},
}

def lookup_driver(model: str) -> dict:
    """Local mock lookup. It never claims values are verified manufacturer specifications."""
    key = (model or "").strip().lower()
    if key in DEMO_DRIVERS:
        return dict(DEMO_DRIVERS[key])
    return {"model": model or "", "found": False, "Fs": 28.0, "Qts": 0.42, "Vas": 60.0, "Re": 3.6, "Xmax": 8.0}

def wavelength(freq_hz: float, speed: float = SPEED_OF_SOUND) -> float:
    if freq_hz <= 0: raise ValueError("Frequency must be positive.")
    return speed / freq_hz

def room_axial_modes(length_m: float, width_m: float, height_m: float, max_order: int = 4):
    """Return (axis, order, Hz) ideal axial modes."""
    if min(length_m, width_m, height_m) <= 0:
        raise ValueError("Room dimensions must be positive.")
    modes = []
    for axis, dim in (("Length", length_m), ("Width", width_m), ("Height", height_m)):
        for n in range(1, max_order + 1):
            modes.append((axis, n, SPEED_OF_SOUND * n / (2 * dim)))
    return sorted(modes, key=lambda x: x[2])

def sabine_rt60(volume_m3: float, absorption_sabins: float) -> float:
    """Estimate mid-band reverberation time using Sabine: RT60 = 0.161 V / A."""
    if volume_m3 <= 0 or absorption_sabins <= 0:
        raise ValueError("Room volume and equivalent absorption area must be positive.")
    return 0.161 * volume_m3 / absorption_sabins


def estimate_sealed_box(fs_hz: float, qts: float, vas_l: float, target_qtc: float = 0.707):
    """Classic sealed-box approximation: Qtc = Qts*sqrt(1+Vas/Vb)."""
    if fs_hz <= 0 or qts <= 0 or vas_l <= 0 or target_qtc <= qts:
        raise ValueError("Need positive Fs/Qts/Vas and target Qtc greater than Qts.")
    vb = vas_l / ((target_qtc / qts) ** 2 - 1)
    fc = fs_hz * math.sqrt(1 + vas_l / vb)
    return {"vb_l": vb, "qtc": target_qtc, "fc_hz": fc}

def estimate_ported_box(fs_hz: float, qts: float, vas_l: float):
    """Rough QB3-like screening estimate; not a substitute for full alignment modelling."""
    if min(fs_hz, qts, vas_l) <= 0:
        raise ValueError("Fs, Qts and Vas must be positive.")
    # Empirical approximation used only as a starting point.
    alpha = max(2.0, min(20.0, 15.0 * (qts ** 2.0)))
    vb = vas_l / alpha
    fb = fs_hz * (0.42 / max(qts, 0.2)) ** 0.35
    return {"vb_l": vb, "fb_hz": fb, "alignment": "rough screening estimate"}

def port_length_cm(area_cm2: float, vb_l: float, fb_hz: float, end_correction_factor: float = 0.732):
    """Round-port estimate in cm; end_correction_factor multiplies port diameter."""
    if not all(math.isfinite(value) for value in (area_cm2, vb_l, fb_hz, end_correction_factor)):
        raise ValueError("Port dimensions, tuning frequency and end correction must be finite.")
    if area_cm2 <= 0 or vb_l <= 0 or fb_hz <= 0 or end_correction_factor < 0:
        raise ValueError("Port area, box volume and tuning frequency must be positive; end correction cannot be negative.")
    # Convert area to equivalent round-port diameter, then apply the standard
    # diameter-based approximation. 23562.5 assumes D in cm and Vb in litres.
    diameter_cm = math.sqrt(4.0 * area_cm2 / math.pi)
    length = (23562.5 * diameter_cm**2 / (fb_hz**2 * vb_l)) - end_correction_factor * diameter_cm
    return max(0.0, length)

def round_port_end_clearance_cm(internal_depth_cm: float, port_length_cm_value: float) -> float:
    """Return remaining axial clearance between a straight port end and rear wall."""
    values = (internal_depth_cm, port_length_cm_value)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Port depth and length must be finite.")
    if internal_depth_cm <= 0 or port_length_cm_value < 0:
        raise ValueError("Internal depth must be positive and port length cannot be negative.")
    return internal_depth_cm - port_length_cm_value


def gross_enclosure_volume_l(
    net_volume_l: float,
    driver_displacement_l: float = 0.0,
    bracing_displacement_l: float = 0.0,
    port_area_cm2: float = 0.0,
    port_length_cm_value: float = 0.0,
) -> dict:
    """Estimate gross internal volume including driver, bracing and straight-port displacement."""
    values = (net_volume_l, driver_displacement_l, bracing_displacement_l,
              port_area_cm2, port_length_cm_value)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Enclosure volumes and port dimensions must be finite.")
    if net_volume_l <= 0 or any(value < 0 for value in values[1:]):
        raise ValueError("Net volume must be positive; displacement and port dimensions cannot be negative.")
    port_displacement_l = port_area_cm2 * port_length_cm_value / 1000.0
    return {
        "port_displacement_l": port_displacement_l,
        "gross_volume_l": net_volume_l + driver_displacement_l
        + bracing_displacement_l + port_displacement_l,
    }


def rectangular_enclosure_dimensions(
    gross_volume_l: float,
    panel_thickness_mm: float = 18.0,
    width_height_ratio: float = 1.5,
    depth_height_ratio: float = 1.0,
) -> dict:
    """Suggest a rectangular enclosure size and simple six-panel cut list."""
    values = (gross_volume_l, panel_thickness_mm, width_height_ratio, depth_height_ratio)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Enclosure dimensions must be finite.")
    if gross_volume_l <= 0 or panel_thickness_mm <= 0 or width_height_ratio <= 0 or depth_height_ratio <= 0:
        raise ValueError("Volume, panel thickness and dimension ratios must be positive.")
    internal_height_cm = (gross_volume_l * 1000 / (width_height_ratio * depth_height_ratio)) ** (1 / 3)
    internal_width_cm = internal_height_cm * width_height_ratio
    internal_depth_cm = internal_height_cm * depth_height_ratio
    thickness_cm = panel_thickness_mm / 10
    external_width_cm = internal_width_cm + 2 * thickness_cm
    external_height_cm = internal_height_cm + 2 * thickness_cm
    external_depth_cm = internal_depth_cm + 2 * thickness_cm
    return {
        "internal_width_cm": internal_width_cm,
        "internal_height_cm": internal_height_cm,
        "internal_depth_cm": internal_depth_cm,
        "external_width_cm": external_width_cm,
        "external_height_cm": external_height_cm,
        "external_depth_cm": external_depth_cm,
        "front_back_panels": (external_width_cm, external_height_cm, 2),
        "top_bottom_panels": (internal_width_cm, internal_depth_cm, 2),
        "side_panels": (internal_depth_cm, internal_height_cm, 2),
    }


def port_velocity(power_w: float, sd_cm2: float, xmax_mm: float, freq_hz: float, port_area_cm2: float):
    """Very simplified sinusoidal volume-velocity estimate; needs real driver parameters."""
    if min(power_w, sd_cm2, xmax_mm, freq_hz, port_area_cm2) <= 0:
        raise ValueError("All inputs must be positive.")
    # Cone peak displacement volume (m^3), then peak velocity through port.
    displacement_m3 = sd_cm2 * 1e-4 * xmax_mm * 1e-3
    volume_velocity_m3_s = 2 * math.pi * freq_hz * displacement_m3
    return volume_velocity_m3_s / (port_area_cm2 * 1e-4)

def placement_guidance(front_wall_m, side_wall_m, listening_distance_m, compromised, use_case):
    front = max(0.2, front_wall_m)
    side = max(0.3, side_wall_m)
    toe = 10 if use_case == "Casual listening" else 15
    if listening_distance_m < 1.5: toe = 5
    lines = [
        f"Start with speaker baffles about {front:.2f} m from the front wall and cabinets at least {side:.2f} m from side walls, if practical.",
        f"Start with approximately {toe}° toe-in per speaker, then adjust in 2–3° steps for centre image and treble balance.",
        f"Begin with an approximately equilateral speaker/listener triangle; listening distance entered: {listening_distance_m:.2f} m.",
        "Measure bass response at the listening seat and several nearby positions before applying EQ."
    ]
    if compromised:
        lines += [
            "If the speakers must stay close to a wall, prioritise symmetry and keep the left/right boundary distances similar.",
            "Try manufacturer-approved port plugs for rear-ported speakers; plugging changes bass alignment and is not universally beneficial.",
            "Use measured parametric EQ cuts for strong peaks; avoid large boosts into cancellation nulls.",
            "Move the listening seat in small increments (10–20 cm) to find smoother bass."
        ]
    return "\n".join("- " + line for line in lines)
