@echo off
title Universal Media Downloader
echo ========================================================
echo   Memulai Universal Media Downloader...
echo ========================================================
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py
) else (
    python run.py
)
pause
