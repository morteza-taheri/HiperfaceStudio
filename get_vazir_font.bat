@echo off
setlocal
cd /d "%~dp0"
if not exist "fonts" mkdir "fonts"
set "BASE=https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf"
for %%F in (Vazirmatn-Regular.ttf Vazirmatn-Bold.ttf) do (
    if not exist "fonts\%%F" (
        echo Downloading %%F ...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "try { [Net.ServicePointManager]::SecurityProtocol = 3072; (New-Object Net.WebClient).DownloadFile('%BASE%/%%F', 'fonts\%%F'); exit 0 } catch { exit 1 }" >nul 2>&1
        if not exist "fonts\%%F" curl -L -s -o "fonts\%%F" "%BASE%/%%F" >nul 2>&1
        if exist "fonts\%%F" (echo   OK) else (echo   [WARNING] could not download %%F. Get it from https://github.com/rastikerdar/vazirmatn)
    )
)
exit /b 0
