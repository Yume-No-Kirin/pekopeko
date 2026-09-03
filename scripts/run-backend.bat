@echo off
REM Launches the Flask API (src/app/api/app.py) from the repo root, so the
REM relative imports under src/app work (must run as `python -m`, not as a
REM script path). Invoked by start-pekopeko.bat, which has already exported
REM PEKOPEKO_VAULT_ROOT / PEKOPEKO_API_KEY into this process's environment.
cd /d "%~dp0.."
python -m src.app.api.app
