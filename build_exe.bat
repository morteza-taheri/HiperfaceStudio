@echo off
setlocal
cd /d "%~dp0"
title HIPERFACE Studio - build EXE

echo ==========================================================
echo   HIPERFACE Studio  -  one-click EXE builder
echo ==========================================================
echo.

set "PY="
py -3.8-64 -c "import sys" >nul 2>&1 && set "PY=py -3.8-64"
if not defined PY py -3.8 -c "import sys" >nul 2>&1 && set "PY=py -3.8"
if not defined PY python -c "import sys" >nul 2>&1 && set "PY=python"
if not defined PY goto :nopython

echo Using:
%PY% -c "import sys, platform; print(sys.version.split()[0], platform.architecture()[0])"
echo.

set "PIN=pyinstaller==5.13.2"
%PY% -c "import sys, struct; sys.exit(0 if sys.version_info[:2] == (3, 8) and struct.calcsize('P') == 8 else 1)"
if errorlevel 1 goto :not38
goto :build

:not38
set "PIN=pyinstaller"
echo [WARNING] This is NOT Python 3.8 64-bit.
echo           The EXE will work on Windows 10/11 but NOT on Windows 7.
echo           For Windows 7 support install Python 3.8.10 64-bit and run again.
echo.
timeout /t 6

:build
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY% -m venv .venv || goto :fail
)
call ".venv\Scripts\activate.bat" || goto :fail

echo Installing pyserial + %PIN% ...
python -m pip install --disable-pip-version-check -q pyserial==3.5 %PIN% || goto :fail

set "PDFARG="
if exist "*im0064865*.pdf" (
    set "PDFARG=--add-data *im0064865*.pdf;."
    echo HIPERFACE specification PDF found: it will be bundled inside the EXE.
) else (
    echo [INFO] Specification PDF not found next to this script. Help will use the online version.
)

if not exist "fonts\Vazirmatn-Regular.ttf" call "%~dp0get_vazir_font.bat"
set "FONTARG="
if exist "fonts\*.ttf" (
    set "FONTARG=--add-data fonts;fonts"
    echo Vazirmatn font found: it will be bundled inside the EXE.
) else (
    echo [INFO] fonts\Vazirmatn-*.ttf not found. Persian UI will fall back to Tahoma.
)

echo Building EXE ...
pyinstaller --noconfirm --clean --onefile --windowed --name HiperfaceStudio --icon app.ico --add-data "app.ico;." %PDFARG% %FONTARG% hiperface_studio.py || goto :fail

copy /y "dist\HiperfaceStudio.exe" "HiperfaceStudio.exe" >nul
echo.
echo ==========================================================
echo   DONE:  %CD%\HiperfaceStudio.exe
echo ==========================================================
pause
exit /b 0

:nopython
echo [ERROR] Python was not found.
echo Install Python 3.8.10 64-bit (last version that supports Windows 7):
echo   https://www.python.org/downloads/release/python-3810/
echo   file: "Windows x86-64 executable installer"
echo   tick "Add Python 3.8 to PATH" during setup.
pause
exit /b 1

:fail
echo.
echo [ERROR] Build failed. Scroll up to see the reason.
pause
exit /b 1
