@echo off
rem Design mode: double-click to edit the rooms. Keep this window open while you work; close it to stop.
cd /d "%~dp0.."
python tools\design_server.py
if errorlevel 1 pause
