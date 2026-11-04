import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from acoustics import (
    wavelength, room_axial_modes, sabine_rt60, estimate_sealed_box, estimate_ported_box,
    port_length_cm, port_velocity, placement_guidance, lookup_driver
)

st.set_page_config(page_title="AcoustiSync", page_icon="🔊", layout="wide")
st.title("AcoustiSync")
st.caption("Audio setup assistant • Room acoustics • DIY enclosure design")
mode = st.radio("Choose your audio environment", ["HOME AUDIO", "CAR AUDIO"], horizontal=True)
st.divider()

def draw_room(room_l, room_w, front_wall_m, side_wall_m, listening_distance_m):
    """Draw a dimensionally scaled top-down plan using the entered room measurements."""
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-0.55, room_w + 0.35)
    ax.set_ylim(-0.55, room_l + 0.55)

    # Room outline: width is the horizontal axis; length is the vertical axis.
    ax.add_patch(plt.Rectangle((0, 0), room_w, room_l, fill=False,
                               edgecolor="black", linewidth=2.2))
    ax.text(room_w / 2, room_l + 0.38, f"BACK WALL  •  {room_w:.2f} m wide",
            ha="center", va="center", fontsize=8)
    ax.text(room_w / 2, -0.34, "FRONT WALL", ha="center", va="center",
            fontsize=8, weight="bold")

    # Keep the plan physically inside the room if a requested wall clearance
    # cannot fit; show the effective clearance used in the drawing.
    effective_side = min(max(0.12, side_wall_m), max(0.12, (room_w - 0.28) / 2))
    effective_front = min(max(0.12, front_wall_m), max(0.12, room_l - 0.55))
    speaker_y = effective_front
    left_x, right_x = effective_side, room_w - effective_side

    # Small top-down speaker cabinet icons. The two drivers are decorative
    # symbols; cabinet positions are plotted at their calculated coordinates.
    cabinet_w, cabinet_d = 0.22, 0.30
    for x, label in ((left_x, "LEFT"), (right_x, "RIGHT")):
        ax.add_patch(plt.Rectangle((x - cabinet_w / 2, speaker_y - cabinet_d / 2),
                                   cabinet_w, cabinet_d, facecolor="#dce7f2",
                                   edgecolor="#24445f", linewidth=1.4, zorder=4))
        ax.add_patch(plt.Circle((x, speaker_y + 0.055), 0.047,
                                facecolor="#6c8297", edgecolor="#20384d",
                                linewidth=0.8, zorder=5))
        ax.add_patch(plt.Circle((x, speaker_y - 0.075), 0.025,
                                facecolor="#6c8297", edgecolor="#20384d",
                                linewidth=0.8, zorder=5))
        ax.text(x, speaker_y + 0.22, f"{label} SPEAKER",
                ha="center", va="bottom", fontsize=7, weight="bold")

    requested_listener_y = speaker_y + listening_distance_m
    listener_y = min(requested_listener_y, room_l - 0.45)
    listener_y = max(speaker_y + 0.35, listener_y)
    listener_x = room_w / 2
    if listener_y > speaker_y:
        ax.annotate("", xy=(listener_x, listener_y), xytext=(listener_x, speaker_y),
                    arrowprops=dict(arrowstyle="<->", color="#536b80", lw=1.1))
        ax.text(listener_x + 0.10, (listener_y + speaker_y) / 2,
                f"{listener_y - speaker_y:.2f} m",
                fontsize=7, va="center", color="#34495e")

    # Listening seat icon.
    seat_w, seat_d = min(0.95, room_w * 0.42), 0.38
    ax.add_patch(plt.Rectangle((listener_x - seat_w / 2, listener_y - seat_d / 2),
                               seat_w, seat_d, facecolor="#eee4d5",
                               edgecolor="#735f48", linewidth=1.3, zorder=3))
    ax.text(listener_x, listener_y, "LISTENING POSITION",
            ha="center", va="center", fontsize=6.5, zorder=6)

    # Dimension lines and labels.
    ax.annotate("", xy=(0, room_l + 0.15), xytext=(room_w, room_l + 0.15),
                arrowprops=dict(arrowstyle="<->", color="#333333", lw=1))
    ax.text(room_w / 2, room_l + 0.19, f"{room_w:.2f} m",
            ha="center", va="bottom", fontsize=8)
    ax.annotate("", xy=(-0.22, 0), xytext=(-0.22, room_l),
                arrowprops=dict(arrowstyle="<->", color="#333333", lw=1))
    ax.text(-0.29, room_l / 2, f"{room_l:.2f} m",
            ha="center", va="center", rotation=90, fontsize=8)

    # Speaker separation is an actual coordinate-derived measurement.
    ax.annotate("", xy=(left_x, speaker_y - 0.25),
                xytext=(right_x, speaker_y - 0.25),
                arrowprops=dict(arrowstyle="<->", color="#536b80", lw=1))
    ax.text(room_w / 2, speaker_y - 0.29, f"Speaker separation: {right_x-left_x:.2f} m",
            ha="center", va="top", fontsize=7, color="#34495e")

    ax.set_xlabel("Room width (m)")
    ax.set_ylabel("Room length (m)")
    ax.set_xticks(np.arange(0, room_w + 0.01, 0.5))
    ax.set_yticks(np.arange(0, room_l + 0.01, 0.5))
    ax.grid(True, alpha=.18, linewidth=0.5)
    ax.set_title("Scaled top-down room plan", fontsize=10, pad=12)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    if requested_listener_y > room_l - 0.45:
        st.warning(
            f"The requested {listening_distance_m:.2f} m listening distance does not fit "
            "inside this room with clearance behind the seat. The drawing places the seat "
            "at the nearest practical position; increase room length or reduce the distance."
        )
    if effective_side != side_wall_m or effective_front != front_wall_m:
        st.caption(
            "A requested wall clearance was constrained to keep the speaker icons inside "
            "the measured room boundary. Check the displayed positions before installation."
        )


def draw_mode_field_3d(room_l, room_w, room_h, axis, order):
    """Illustrative 3D pressure field for one ideal axial room mode."""
    x = np.linspace(0, room_l, 8)
    y = np.linspace(0, room_w, 6)
    z = np.linspace(0, room_h, 5)
    xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")
    dimension = {"Length": room_l, "Width": room_w, "Height": room_h}[axis]
    coordinate = {"Length": xx, "Width": yy, "Height": zz}[axis]
    pressure = np.cos(order * np.pi * coordinate / dimension)

    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot(111, projection="3d")
    points = ax.scatter(
        xx.ravel(), yy.ravel(), zz.ravel(),
        c=pressure.ravel(), cmap="coolwarm", vmin=-1, vmax=1,
        s=24, alpha=0.85
    )
    ax.set_xlabel("Length (m)")
    ax.set_ylabel("Width (m)")
    ax.set_zlabel("Height (m)")
    ax.set_title(f"Ideal {axis.lower()} axial mode {order}")
    fig.colorbar(points, ax=ax, shrink=0.65, label="Relative pressure")
    st.pyplot(fig)
    plt.close(fig)


if mode == "HOME AUDIO":
    task = st.radio("Home audio workflow", ["Finished speaker setup", "Driver-in-hand / DIY enclosure"], horizontal=True)
    if task == "Finished speaker setup":
        st.subheader("Finished speaker placement")
        st.caption("Change the measurements below to match your own room. Starting values are examples, not locked settings.")
        c1, c2 = st.columns(2)
        with c1:
            speakers = st.text_input("Speaker model", "Mission floorstanders")
            amp = st.text_input("Amplifier / receiver", "Sony receiver")
            room_l = st.number_input("Room length (m)", 2.0, 20.0, 5.0, .1)
            room_w = st.number_input("Room width (m)", 2.0, 15.0, 3.8, .1)
            room_h = st.number_input("Ceiling height (m)", 2.0, 6.0, 2.5, .1)
        with c2:
            use_case = st.selectbox("Main use", ["Music", "Movies / Dolby Pro Logic", "Casual listening"])
            front_wall = st.number_input("Available speaker distance from front wall (m)", .05, 2.0, .45, .05)
            side_wall = st.number_input("Available distance from side wall (m)", .05, 2.0, .6, .05)
            listening_distance = st.number_input("Listening distance (m)", 1.0, 8.0, 2.5, .1)
            compromised = st.checkbox("Compromised setup: speakers cannot be moved far from walls")
        st.markdown("Room boundaries")
        walls = st.selectbox("Wall construction", ["Brick / concrete", "Plasterboard / hollow wall", "Mixed"])
        floor_type = st.selectbox("Floor finish", ["Carpet", "Wood / tile", "Thick rug"])
        ceiling_type = st.selectbox("Ceiling finish", ["Plaster / concrete", "Acoustic ceiling"])
        furniture = st.text_input("Furniture / obstacles", "Sofa between speakers; bookcase on side wall")
        furniture_sabins = st.number_input(
            "Additional furnishings absorption (Sabins)", 0.0, 100.0, 8.0, 1.0
        )
        mode_axis = st.selectbox("3D axial mode to inspect", ["Length", "Width", "Height"])
        mode_order = st.selectbox("Mode order", [1, 2, 3, 4])
        if st.button("Calculate placement plan", type="primary"):
            st.write(f"**System:** {speakers} with {amp}. Use case: {use_case}.")
            st.write(placement_guidance(front_wall, side_wall, listening_distance, compromised, use_case))
            st.subheader("What this means in your room")
            st.write("The room dimensions and speaker distances you entered are used for these estimates. Change the measurements above and calculate again to compare options.")
            modes = room_axial_modes(room_l, room_w, room_h)
            st.markdown("**Possible bass build-up points**")
            st.caption("These are frequencies where the room may make bass sound louder or quieter in certain places. They are not faults in the speakers.")
            st.dataframe([{"Room direction": a, "Pattern": f"Mode {n}", "Possible bass frequency": f"{f:.1f} Hz"} for a,n,f in modes[:6]], use_container_width=True, hide_index=True)
            wall_alpha = {"Brick / concrete": 0.03, "Plasterboard / hollow wall": 0.05, "Mixed": 0.04}[walls]
            floor_alpha = {"Carpet": 0.25, "Wood / tile": 0.05, "Thick rug": 0.35}[floor_type]
            ceiling_alpha = {"Plaster / concrete": 0.05, "Acoustic ceiling": 0.55}[ceiling_type]
            wall_area = 2 * (room_l * room_h + room_w * room_h)
            floor_area = room_l * room_w
            absorption_sabins = (
                wall_area * wall_alpha
                + floor_area * floor_alpha
                + floor_area * ceiling_alpha
                + furniture_sabins
            )
            rt60 = sabine_rt60(room_l * room_w * room_h, absorption_sabins)
            st.write(f"**Estimated room echo time: {rt60:.2f} seconds**")
            if rt60 < 0.3:
                st.success("Plain meaning: this estimate suggests a fairly controlled room with relatively little lingering sound.")
            elif rt60 < 0.6:
                st.info("Plain meaning: this estimate suggests a moderate amount of room echo. Whether it sounds right depends on room size, furnishings and preference.")
            else:
                st.warning("Plain meaning: this estimate suggests sound may linger noticeably. Soft furnishings, rugs or curtains may help, depending on the actual room.")
            st.caption(
                f"Estimated equivalent absorption: {absorption_sabins:.1f} Sabins. "
                "Material coefficients are broad assumptions; this is not a measured RT60."
            )
            with st.expander("Technical view: 3D room-mode model"):
                draw_mode_field_3d(room_l, room_w, room_h, mode_axis, mode_order)
                st.caption("This colour plot is a simplified pressure pattern, not a measured sound map. Red and blue indicate opposite pressure phases; neither means good or bad.")
            st.markdown("**Suggested starting layout**")
            st.caption(
                f"Scaled to the room dimensions entered above: {room_w:.2f} m wide × "
                f"{room_l:.2f} m long × {room_h:.2f} m high. Speaker and seat symbols "
                "show calculated plan positions, not the physical cabinet dimensions."
            )
            draw_room(room_l, room_w, front_wall, side_wall, listening_distance)
            st.info("**In practical terms:** start with the suggested positions, listen for uneven bass or a weak centre image, then move speakers in small steps. The calculation cannot hear your room. A microphone measurement is needed for a reliable final adjustment.")
            if compromised:
                st.write("- Try the manufacturer's foam port plug if the speaker has a rear port.")
                st.write("- Avoid placing the listening seat exactly halfway between front and rear walls.")
                st.write("- Use room correction or careful parametric EQ for measured peaks; do not boost deep nulls.")
                st.write("- Consider a higher subwoofer crossover if mains struggle near boundaries; verify integration and phase.")
            st.caption(f"Speed of sound assumed 343 m/s. At 80 Hz, wavelength ≈ {wavelength(80):.2f} m.")
    else:
        st.subheader("Home DIY enclosure calculator")
        st.caption("All inputs can be edited. Enter the figures from your driver datasheet; starting values are examples only.")
        model = st.text_input("Driver model", "Mission Subwoofer Driver")
        if st.button("Look up driver"):
            record = lookup_driver(model)
            st.session_state["driver_lookup"] = record
        rec = st.session_state.get("driver_lookup", lookup_driver(""))
        if rec and rec.get("found"):
            st.success(f"Demo catalogue match: {rec['model']} — values are illustrative, not verified manufacturer data.")
        else:
            st.warning("No verified driver record found. Enter values from the manufacturer datasheet or measure them.")
        with st.form("home_ts"):
            a,b,c = st.columns(3)
            fs = a.number_input("Fs (Hz)", 10.0, 200.0, float(rec.get("Fs", 28.0)), .5)
            qts = b.number_input("Qts", .1, 1.5, float(rec.get("Qts", .42)), .01)
            vas = c.number_input("Vas (litres)", 1.0, 1000.0, float(rec.get("Vas", 60.0)), 1.0)
            xmax = a.number_input("Xmax (mm, one-way)", 1.0, 40.0, float(rec.get("Xmax", 8.0)), .5)
            re = b.number_input("Re (ohms)", 1.0, 16.0, float(rec.get("Re", 3.6)), .1)
            wood = c.number_input("Panel thickness (mm)", 9.0, 30.0, 18.0, 1.0)
            driver_disp = a.number_input("Driver displacement (litres)", 0.0, 20.0, .8, .1)
            brace_disp = b.number_input("Bracing displacement (litres)", 0.0, 20.0, 1.0, .1)
            target_fb = c.number_input("Ported tuning target Fb (Hz)", 18.0, 80.0, 30.0, .5)
            port_d = c.number_input("Round port inside diameter (cm)", 3.0, 20.0, 10.0, .5)
            submitted = st.form_submit_button("Design enclosure", type="primary")
        if submitted:
            ported = estimate_ported_box(fs, qts, vas)
            st.subheader("Initial alignment estimates")
            st.write(
                f"**Driver inputs:** {model} · Fs {fs:.1f} Hz · Qts {qts:.2f} · "
                f"Vas {vas:.1f} L · Re {re:.1f} Ω · Xmax {xmax:.1f} mm."
            )
            try:
                sealed = estimate_sealed_box(fs, qts, vas)
                st.write(f"**Sealed box starting estimate: {sealed['vb_l']:.1f} litres of usable internal space.**")
                st.caption(f"Estimated damping factor (Qtc): {sealed['qtc']:.2f}. This is a technical design value, not a sound-quality score.")
            except ValueError:
                st.warning(
                    "A sealed alignment targeting Qtc 0.707 cannot be calculated when "
                    "the entered Qts is 0.707 or higher. Review the driver data or use "
                    "a different target alignment in a dedicated simulator."
                )
            st.write(f"**Ported box starting estimate: {ported['vb_l']:.1f} litres of usable internal space.**")
            st.caption(f"The rough model tuning estimate is {ported['fb_hz']:.1f} Hz. The port dimensions below use your selected target of {target_fb:.1f} Hz.")
            st.caption("These are screening estimates, not a validated alignment. Final design needs full T/S data (including Qes/Qms, Sd, Pe and excursion), response modelling, and measurement.")
            net = ported["vb_l"]
            gross = net + driver_disp + brace_disp
            area = 3.14159 * (port_d/2)**2
            length = port_length_cm(area, net, target_fb)
            st.write(f"**Port tube starting size: {port_d:.1f} cm inside diameter and approximately {length:.1f} cm long.**")
            st.caption("The port is the air tube in the box. Its size affects bass tuning. Final length may need adjustment for flares, bends and the actual box.")
            st.write(f"**Volume:** {net:.1f} L net; estimated gross internal volume {gross:.1f} L after adding driver/bracing displacement.")
            st.write(f"**Air velocity check:** requires amplifier power, Sd, and excursion model; not inferred from T/S values alone. Avoid assuming this port is quiet at high output.")
            st.write(f"**Panel basis:** {wood:.0f} mm material. External rectangular dimensions add {2 * wood:.0f} mm to each corresponding internal dimension.")
            st.write("**Cutting-sheet basis:** choose internal dimensions that multiply to gross volume (L × W × H / 1000 = litres). Include bracing, driver cutout, port path, and assembly method before cutting.")
            st.warning("Do not cut wood from these preliminary estimates without verifying driver datasheet values, port end corrections, fitment, and the final net-volume calculation.")

else:
    task = st.radio("Car audio workflow", ["Subwoofer enclosure builder", "Component speaker placement"], horizontal=True)
    if task == "Subwoofer enclosure builder":
        st.subheader("Car subwoofer enclosure builder")
        st.caption("Change the vehicle space and subwoofer measurements to match your own installation. Starting values are examples only.")
        c1,c2 = st.columns(2)
        with c1:
            model = st.text_input("Subwoofer model", "Example 12-inch subwoofer")
            vehicle = st.selectbox("Vehicle body", ["Hatchback", "Sedan", "SUV", "Truck"])
            trunk_l = st.number_input("Available width (cm)", 30.0, 160.0, 90.0, 1.0)
            trunk_h = st.number_input("Available height (cm)", 20.0, 100.0, 38.0, 1.0)
            trunk_d = st.number_input("Available depth (cm)", 20.0, 100.0, 40.0, 1.0)
        with c2:
            fs = st.number_input("Fs (Hz)", 10.0, 200.0, 30.0, .5)
            qts = st.number_input("Qts", .1, 1.5, .42, .01)
            vas = st.number_input("Vas (litres)", 1.0, 1000.0, 50.0, 1.0)
            xmax = st.number_input("Xmax (mm, one-way)", 1.0, 40.0, 12.0, .5)
            target_fb = st.number_input("Target tuning Fb (Hz)", 20.0, 50.0, 32.0, .5)
            port_d = st.number_input("Round port diameter (cm)", 5.0, 18.0, 10.0, .5)
        if st.button("Calculate car enclosure", type="primary"):
            result = estimate_ported_box(fs, qts, vas)
            net = result["vb_l"]
            gross = net + 1.5
            area = 3.14159 * (port_d/2)**2
            length = port_length_cm(area, net, target_fb)
            max_l = trunk_l/100
            max_h = trunk_h/100
            max_d = trunk_d/100
            fit_l = max_l*max_h*max_d*1000
            st.write(f"**Subwoofer:** {model} · Fs {fs:.1f} Hz · Qts {qts:.2f} · Vas {vas:.1f} L · Xmax {xmax:.1f} mm.")
            st.write(f"**Estimated usable box space: {net:.1f} litres.** Allowing 1.5 litres for the driver and internal parts gives an estimated gross requirement of {gross:.1f} litres.")
            st.write(f"**Port tube starting size: {port_d:.1f} cm diameter × {length:.1f} cm long**, estimated for your selected {target_fb:.1f} Hz target.")
            st.caption(f"The simplified driver model estimates a tuning point near {result['fb_hz']:.1f} Hz before applying your selected port target.")
            st.write(f"**Available rectangular envelope:** approximately {fit_l:.1f} L gross before taper, wheel arches, trim, and clearance.")
            if gross > fit_l:
                st.error("The estimated box volume exceeds the rectangular envelope. Recalculate with a smaller alignment or different enclosure approach.")
            st.write("**Orientation starting point:**")
            st.write({"Hatchback":"Subwoofer and port rear-facing is a common starting experiment; test rear-facing versus upward-facing.","Sedan":"Rear-facing can work, but cabin coupling through the rear seat/pass-through strongly affects results.","SUV":"Rear-facing or upward-facing; compare response at the driver seat.","Truck":"Fitment and seat/wall coupling dominate; test the available orientations."}[vehicle])
            st.info("Cabin gain is vehicle-specific and cannot be accurately calculated from body style alone. No automatic +12 dB/octave correction is applied: measure in-car response or use a measured transfer function before EQ.")
            st.warning("Port air speed/chuffing cannot be checked reliably without amplifier power, driver Sd, excursion and a defined signal/model. Use a flare and adequate port area; verify with modelling and measurement.")
    else:
        st.subheader("Car component placement")
        st.caption("Choose the options that match your vehicle and speaker installation.")
        speaker = st.text_input("Component speaker model", "Component 6.5-inch set")
        tweeter = st.selectbox("Tweeter location", ["A-pillar", "Dash", "Sail panel", "Factory location"])
        driver_side = st.selectbox("Driver position", ["Left-hand drive", "Right-hand drive"], index=1)
        if st.button("Generate staging advice", type="primary"):
            st.write(f"For {speaker}, begin with tweeters at {tweeter.lower()} and aim them for a controlled comparison rather than assuming on-axis is always best.")
            st.write(f"Vehicle: {driver_side}. Use the DSP to align arrival time at the driver's head position; start with measured distances and refine by listening/impulse response.")
            st.write("- Keep left/right tweeter aiming and crossover settings deliberate; avoid obstructing airbags.")
            st.write("- Check polarity, crossover slopes, and level matching before changing EQ.")
            st.write("- Secure components against vibration and follow vehicle safety requirements.")

with st.expander("Engineering assumptions and limitations"):
    st.markdown("""
- This is a planning calculator, not an anechoic prediction or professional design sign-off.
- Online lookup is represented by a local demo catalogue; no live manufacturer database is queried.
- Never label demo data as manufacturer-verified. Confirm all driver values against the exact revision/datasheet.
- Room modes shown are ideal axial-mode estimates: `f = c/2 × n/dimension`.
- Port length uses a common Helmholtz approximation with a simplified end correction; slot ports need their own effective length and corner/end corrections.
- Boundary gain, SBIR, cabin transfer function, perceived bass and crossover integration depend on geometry and measurements.
- For reliable optimisation, measure with a calibrated microphone and software such as REW; model enclosure response with a dedicated loudspeaker simulator before building.
""")
