@echo off
REM Launches the Vite dev server for frontend/. Invoked by start-pekopeko.bat.
cd /d "%~dp0..\frontend"
call npm run dev
