@echo off
REM Build a single-file Windows executable using PyInstaller
REM Usage: double-click this file or run from cmd in the repo root

python -m pip install -r requirements.txt

REM Create a one-file, windowed exe (no console). Adjust --add-data entries if needed.
pyinstaller --noconfirm --clean --onefile --windowed --add-data "output;output" gui.py

echo Build finished. Dist folder contains the executable.
pause
