# PowerShell build script: installs requirements and runs PyInstaller
# Run from the repository root: Right-click -> Run with PowerShell (or run in an elevated shell if needed)

python -m pip install -r requirements.txt

# On Windows PyInstaller expects add-data in the form "source;dest"
pyinstaller --noconfirm --clean --onefile --windowed --add-data "output;output" gui.py

Write-Host "Build finished. See the 'dist' folder for the executable." -ForegroundColor Green
