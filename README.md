# AcoustiSync

Streamlit-based audio setup assistant for home and car audio.

## Current workflows

- Home audio: finished-speaker placement guidance, ideal axial room-mode frequency estimates, an illustrative 3D axial-mode pressure field, and a room layout diagram.
- Home acoustics: Sabine RT60 screening estimate using room dimensions, selected wall/floor/ceiling finishes, and an adjustable furnishings absorption allowance.
- Home DIY: preliminary sealed and ported enclosure screening calculations, round-port length estimate, and internal/gross volume guidance.
- Car audio: preliminary subwoofer enclosure sizing against a rectangular boot envelope, plus component-speaker staging guidance.

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

## Automated verification

GitHub Actions runs the acoustic calculation tests and Streamlit workflow smoke tests on pushes and pull requests to `main`.

## Engineering limitations

This application is a planning aid, not professional design sign-off. RT60 uses broad, assumed mid-frequency absorption coefficients; actual absorption varies by frequency, material construction, installation, furnishings and room contents. The 3D room-mode view is an idealised axial pressure field, not a measured or full-wave room simulation.

Driver catalogue entries are illustrative and are not verified manufacturer specifications. Round-port length uses an equivalent diameter derived from the entered port area and a conventional end-correction estimate; flares, slot ports, port folding and enclosure-specific end effects still require dedicated modelling. Enclosure estimates require confirmation against the exact driver's datasheet, full Thiele/Small parameters, excursion and port-velocity modelling, physical fitment, and measurement. Room and vehicle acoustic behaviour cannot be fully predicted from the current inputs.

Do not cut enclosure panels or apply aggressive EQ solely from these preliminary estimates.

## Public deployment (release target)

The app is a Python/Streamlit application; GitHub Pages and a plain Cloudflare Worker cannot run this Python entrypoint directly. The intended no-cost first deployment is Streamlit Community Cloud.

Deployment coordinates:
- Repository: `MrP-SOURCE/AcoustiSync`
- Branch: `main`
- Entrypoint: `app.py`
- Dependencies: root `requirements.txt`
- Python: select Python 3.11 in Advanced settings to match CI.

Release procedure:
1. Sign in to Streamlit Community Cloud with the GitHub account that has admin access to this repository.
2. Create an app and select the repository, `main`, and `app.py`.
3. Choose an available public app subdomain.
4. Set the app visibility to public when ready for public distribution.
5. Wait for the build to complete, then test both HOME AUDIO and CAR AUDIO workflows on the hosted URL.

Community Cloud needs GitHub authorisation to access a private repository. Keep the repository private until the app has passed release checks; review the requested GitHub permissions before approving access. A public app must be explicitly made public in its sharing settings.

## Deployment status

The source and automated checks are in active verification. A public deployment should only be announced after the latest CI run, deployment configuration, and live application smoke test have passed.
