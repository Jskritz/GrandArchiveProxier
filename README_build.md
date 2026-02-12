# Building a Windows executable (GUI)

This repository contains a Tkinter GUI (`gui.py`) that launches the printable-card generator.
Below are minimal instructions to create a single-file Windows executable using PyInstaller.

Prerequisites
- Python 3.8+ installed and on `PATH`.
- Recommended to use a virtual environment.

Quick steps (recommended)

1. From the repo root, create and activate a venv (optional but recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install required packages and PyInstaller:

```powershell
python -m pip install -r requirements.txt
```

3. Build the executable using the included scripts:

From PowerShell (preferred):

```powershell
.\build_exe.ps1
```

Or from Command Prompt:

```cmd
build_exe.bat
```

What the build does
- Installs packages from `requirements.txt`.
- Runs PyInstaller to produce a single-file, windowed executable for `gui.py`.
- The produced executable will be in the `dist` folder.

Notes & troubleshooting
- If `printerGA.py` uses additional non-Python assets, you may need to include them with `--add-data`.
- If the app opens console windows unexpectedly, remove `--windowed` from the PyInstaller command to keep the console visible for debugging.
- If the build misses modules at runtime, run PyInstaller once and inspect the generated `.spec` file; add hiddenimports or data files as needed.

If you want, I can try to craft a `gui.spec` file including explicit data files and hidden imports based on `printerGA.py`'s contents — tell me to proceed and I'll scan `printerGA.py` to tailor the spec.
