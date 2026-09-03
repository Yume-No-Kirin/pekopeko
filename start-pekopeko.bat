@echo off
REM One-click launcher: starts the Flask backend (src/app/api/app.py) and the
REM Vite frontend dev server (frontend/), each in its own window, then opens
REM the dashboard in the default browser.
REM
REM First run only: generates a local dev config (PEKOPEKO_VAULT_ROOT under
REM %USERPROFILE%\.pekopeko\vault, a random PEKOPEKO_API_KEY) into
REM .pekopeko-local.env (gitignored) and a matching frontend\.env, since
REM neither exists yet on a fresh checkout and the backend refuses to start
REM without them (src/app/api/settings.py).
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "LOCAL_ENV=%ROOT%\.pekopeko-local.env"

where python >nul 2>nul
if errorlevel 1 (
    echo [pekopeko] ERREUR : python introuvable dans le PATH.
    pause
    exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
    echo [pekopeko] ERREUR : npm introuvable dans le PATH ^(Node.js requis^).
    pause
    exit /b 1
)

if not exist "%LOCAL_ENV%" (
    echo [pekopeko] Premiere execution : generation d'une config locale...
    set "VAULT_DIR=%USERPROFILE%\.pekopeko\vault"
    if not exist "!VAULT_DIR!" mkdir "!VAULT_DIR!"
    for /f "usebackq delims=" %%K in (`powershell -NoProfile -Command "[guid]::NewGuid().ToString('N')"`) do set "APIKEY=%%K"
    (
        echo PEKOPEKO_VAULT_ROOT=!VAULT_DIR!
        echo PEKOPEKO_API_KEY=!APIKEY!
    ) > "%LOCAL_ENV%"
    echo [pekopeko] Config ecrite dans "%LOCAL_ENV%" ^(gitignore^).
)

for /f "usebackq tokens=1,2 delims==" %%A in ("%LOCAL_ENV%") do set "%%A=%%B"

if not exist "%PEKOPEKO_VAULT_ROOT%" mkdir "%PEKOPEKO_VAULT_ROOT%"

if not exist "%ROOT%\frontend\.env" (
    echo [pekopeko] Generation de frontend\.env...
    (
        echo VITE_API_BASE_URL=http://127.0.0.1:5000
        echo VITE_API_KEY=%PEKOPEKO_API_KEY%
    ) > "%ROOT%\frontend\.env"
)

echo [pekopeko] Verification des dependances Python...
python -m pip install -q -r "%ROOT%\src\requirements.txt"
if errorlevel 1 (
    echo [pekopeko] ERREUR : installation des dependances Python echouee.
    pause
    exit /b 1
)

if not exist "%ROOT%\frontend\node_modules" (
    echo [pekopeko] Installation des dependances frontend ^(premiere execution^)...
    pushd "%ROOT%\frontend"
    call npm install
    popd
)

echo [pekopeko] Demarrage du backend ^(Flask, http://127.0.0.1:5000^)...
start "Pekopeko - Backend" cmd /k call "%ROOT%\scripts\run-backend.bat"

echo [pekopeko] Demarrage du frontend ^(Vite, http://localhost:5173^)...
start "Pekopeko - Frontend" cmd /k call "%ROOT%\scripts\run-frontend.bat"

echo [pekopeko] Ouverture du navigateur...
timeout /t 4 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo [pekopeko] Lance. Ferme les fenetres "Pekopeko - Backend" et "Pekopeko - Frontend" pour tout arreter.
