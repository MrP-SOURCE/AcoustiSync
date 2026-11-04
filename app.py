import streamlit as st
import matplotlib.pyplot as plt
from acoustics import (
    wavelength, room_axial_modes, estimate_sealed_box, estimate_ported_box,
    port_length_cm, port_velocity, placement_guidance, lookup_driver
)

st.set_page_config(page_title="AcoustiSync", page_icon="🔊", layout="wide")
st.title("AcoustiSync")
st.caption("Audio setup assistant • Room acoustics • DIY enclosure design")
mode = st.radio("Choose your audio environment", ["HOME AUDIO", "CAR AUDIO"], horizontal=True)
st.divider()

def draw_room(room_l, room_w, sx, sy, lx, ly):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.set_xlim(0, room_l); ax.set_ylim(0, room_w)
    ax.set_aspect("equal", adjustable="box")
    ax.add_patch(plt.Rectangle((0, 0), room_l, room_w, fill=False, linewidth=2))
    ax.scatter([sx], [sy], marker="s", s=100, label="Left speaker")
    ax.scatter([min(room_l-0.1, sx+1.2)], [sy], marker="s", s=100, label="Right speaker (illustrative)")
    ax.scatter([lx], [ly], marker="o", s=110, label="Listening position")
    ax.set_xlabel("Room length (m)"); ax.set_ylabel("Room width (m)")
    ax.grid(True, alpha=.25); ax.legend(loc="upper right")
    st.pyplot(fig)
    plt.close(fig)

if mode == "HOME AUDIO":
    task = st.radio("Home audio workflow", ["Finished speaker setup", "Driver-in-hand / DIY enclosure"], horizontal=True)
    if task == "Finished speaker setup":
        st.subheader("Finished speaker placement")
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
        furniture = st.text_input("Furniture / obstacles", "Sofa between speakers; bookcase on side wall")
        if st.button("Calculate placement plan", type="primary"):
            st.write(f"**System:** {speakers} with {amp}. Use case: {use_case}.")
            st.write(placement_guidance(front_wall, side_wall, listening_distance, compromised, use_case))
            st.write("**Room axial-mode estimates (Hz)**")
            modes = room_axial_modes(room_l, room_w, room_h)
            st.dataframe([{"Axis": a, "Mode": n, "Frequency (Hz)": round(f, 1)} for a,n,f in modes], use_container_width=True)
            st.write("**Room layout (illustrative, not a measured acoustic model)**")
            sx, sy = max(.1, front_wall), max(.1, side_wall)
            draw_room(room_l, room_w, sx, sy, min(room_l-.2, listening_distance+front_wall), room_w/2)
            st.info("SBIR and boundary gain depend on driver geometry, radiation pattern, wall impedance, and exact room layout. Treat these distances as starting points; confirm with measurements/REW and adjust by listening.")
            if compromised:
                st.write("- Try the manufacturer's foam port plug if the speaker has a rear port.")
                st.write("- Avoid placing the listening seat exactly halfway between front and rear walls.")
                st.write("- Use room correction or careful parametric EQ for measured peaks; do not boost deep nulls.")
                st.write("- Consider a higher subwoofer crossover if mains struggle near boundaries; verify integration and phase.")
            st.caption(f"Speed of sound assumed 343 m/s. At 80 Hz, wavelength ≈ {wavelength(80):.2f} m.")
    else:
        st.subheader("Home DIY enclosure calculator")
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
            sealed = estimate_sealed_box(fs, qts, vas)
            ported = estimate_ported_box(fs, qts, vas)
            st.subheader("Initial alignment estimates")
            st.write(f"**Suggested sealed starting point:** {sealed['vb_l']:.1f} L net, estimated Qtc {sealed['qtc']:.2f}.")
            st.write(f"**Ported starting point:** {ported['vb_l']:.1f} L net, approximate Fb {target_fb:.1f} Hz target.")
            st.caption("These are screening estimates, not a validated alignment. Final design needs full T/S data (including Qes/Qms, Sd, Pe and excursion), response modelling, and measurement.")
            net = ported["vb_l"]
            gross = net + driver_disp + brace_disp
            area = 3.14159 * (port_d/2)**2
            length = port_length_cm(area, net, target_fb)
            st.write(f"**Port:** {port_d:.1f} cm internal diameter × {length:.1f} cm calculated straight length (before end correction/flare adjustment).")
            st.write(f"**Volume:** {net:.1f} L net; estimated gross internal volume {gross:.1f} L after adding driver/bracing displacement.")
            st.write(f"**Air velocity check:** requires amplifier power, Sd, and excursion model; not inferred from T/S values alone. Avoid assuming this port is quiet at high output.")
            st.write("**Cutting-sheet basis:** choose internal dimensions that multiply to gross volume (L × W × H / 1000 = litres). For a simple rectangular box, external dimensions add twice the panel thickness to each internal dimension. Include bracing, driver cutout, port path, and assembly method before cutting.")
            st.warning("Do not cut wood from these preliminary estimates without verifying driver datasheet values, port end corrections, fitment, and the final net-volume calculation.")

else:
    task = st.radio("Car audio workflow", ["Subwoofer enclosure builder", "Component speaker placement"], horizontal=True)
    if task == "Subwoofer enclosure builder":
        st.subheader("Car subwoofer enclosure builder")
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
            st.write(f"**Preliminary net volume:** {net:.1f} L; gross estimate with 1.5 L allowance: {gross:.1f} L.")
            st.write(f"**Port:** {port_d:.1f} cm diameter × {length:.1f} cm calculated length for {target_fb:.1f} Hz (before end corrections).")
            st.write(f"**Available rectangular envelope:** approximately {fit_l:.1f} L gross before taper, wheel arches, trim, and clearance.")
            if gross > fit_l:
                st.error("The estimated box volume exceeds the rectangular envelope. Recalculate with a smaller alignment or different enclosure approach.")
            st.write("**Orientation starting point:**")
            st.write({"Hatchback":"Subwoofer and port rear-facing is a common starting experiment; test rear-facing versus upward-facing.","Sedan":"Rear-facing can work, but cabin coupling through the rear seat/pass-through strongly affects results.","SUV":"Rear-facing or upward-facing; compare response at the driver seat.","Truck":"Fitment and seat/wall coupling dominate; test the available orientations."}[vehicle])
            st.info("Cabin gain is vehicle-specific and cannot be accurately calculated from body style alone. No automatic +12 dB/octave correction is applied: measure in-car response or use a measured transfer function before EQ.")
            st.warning("Port air speed/chuffing cannot be checked reliably without amplifier power, driver Sd, excursion and a defined signal/model. Use a flare and adequate port area; verify with modelling and measurement.")
    else:
        st.subheader("Car component placement")
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
