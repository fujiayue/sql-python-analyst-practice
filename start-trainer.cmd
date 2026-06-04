@echo off
setlocal
cd /d "%~dp0"

python "launcher\trainer_launcher.py"
if errorlevel 1 pause

