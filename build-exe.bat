:: Build a distributable Viewline folder (onedir) with PyInstaller.
:: Produces dist\Viewline\ — copy that whole folder to any PC and run Viewline.exe.
:: No Python or dependency install needed on the target machine.

@echo off
setlocal

set "REPO_DIR=%~dp0"
set "VPY=%REPO_DIR%.venv\Scripts\python.exe"

if not exist "%VPY%" (
    echo [ERROR] venv not found. Run setup-viewline.bat first.
    pause
    exit /b 1
)

:: Proxy vars can break pip; clear them (see setup-viewline.bat).
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "http_proxy="
set "https_proxy="

echo Installing PyInstaller into the venv (one-time) ...
"%VPY%" -m pip install pyinstaller
if errorlevel 1 ( echo [ERROR] could not install pyinstaller. & pause & exit /b 1 )

echo Cleaning previous build ...
if exist "%REPO_DIR%build"  rmdir /s /q "%REPO_DIR%build"
if exist "%REPO_DIR%dist"   rmdir /s /q "%REPO_DIR%dist"

echo Building (this takes a few minutes) ...
"%VPY%" -m PyInstaller "%REPO_DIR%viewline.spec" --noconfirm
if errorlevel 1 ( echo [ERROR] build failed. & pause & exit /b 1 )

echo.
echo === Done. Distributable folder: %REPO_DIR%dist\Viewline ===
echo Zip that folder and share it. Target users run Viewline.exe.
echo.
pause
endlocal
