@echo off
title REGWinadmin Launcher

:: --- AUTO-ELEVATE TO ADMIN ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install Python 3.10+ from https://www.python.org and tick "Add Python to PATH".
    pause
    exit /b 1
)

python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
)

echo Starting REGWinadmin...
python main.py
if errorlevel 1 (
    echo.
    echo ERROR: the application failed to start - see the messages above.
    pause
)
