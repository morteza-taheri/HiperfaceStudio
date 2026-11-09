@echo off
cd /d "%~dp0"
if not exist "fonts\Vazirmatn-Regular.ttf" call "%~dp0get_vazir_font.bat"
if exist ".venv\Scripts\pythonw.exe" (start "" ".venv\Scripts\pythonw.exe" hiperface_studio.py) else (python -m pip install -q pyserial==3.5 & start "" pythonw hiperface_studio.py)
