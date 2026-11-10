@echo off
cd /d "%~dp0"
python -m pip install --quiet tkinterdnd2
python conversor_mp4.py
if errorlevel 1 pause
