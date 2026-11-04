# AcoustiSync

Streamlit-based audio setup assistant for home and car audio.

## Current workflows

- Home audio: finished-speaker placement guidance, room axial-mode estimates, and an illustrative room layout.
- Home DIY: preliminary sealed and ported enclosure screening calculations.
- Car audio: preliminary subwoofer enclosure sizing and component-speaker staging guidance.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate the environment, then install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Engineering limitations

This application is a planning aid, not professional design sign-off. Driver catalogue entries are illustrative and are not verified manufacturer specifications. Enclosure estimates require confirmation against the exact driver's datasheet, full Thiele/Small parameters, excursion and port-velocity modelling, physical fitment, and measurement. Room and vehicle acoustic behaviour cannot be fully predicted from the current inputs.

Do not cut enclosure panels or apply aggressive EQ solely from these preliminary estimates.

## Deployment status

The source code is being assembled and verified. A public deployment should only be announced after dependency installation, automated tests, and a live application smoke test have passed.
