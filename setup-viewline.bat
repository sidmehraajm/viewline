:: Viewline one-time setup (Python 3.10, images + movies, no USD)
:: Creates an isolated virtual environment and installs all dependencies.
:: Run this ONCE. After it finishes, use run-viewline.bat to launch.

@echo off
setlocal

:: --- Point this at your Python 3.10 if "py -3.10" does not work ---
set "PYEXE=py -3.10"

:: ============================================================
::  PROXY HANDLING
::  Your last run failed with "check_hostname requires server_hostname".
::  That means a proxy env var was set (badly). By default we CLEAR it
::  so pip connects directly. If your studio REQUIRES a proxy, comment
::  out the four "set ..._PROXY=" clear lines below and fill in PIP_PROXY.
:: ============================================================
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "http_proxy="
set "https_proxy="

:: If a proxy IS required, put it here as http://host:port (note: http, not https)
::   and pip will use it. Leave empty to connect directly.
set "PIP_PROXY="

if defined PIP_PROXY (
    set "PROXY_ARG=--proxy %PIP_PROXY%"
) else (
    set "PROXY_ARG="
)

echo.
echo === Viewline setup ===
echo.

%PYEXE% --version 2>NUL
if errorlevel 1 (
    echo [ERROR] Python 3.10 not found via "%PYEXE%".
    echo Edit setup-viewline.bat and set PYEXE to your python.exe path, e.g.
    echo     set "PYEXE=C:/Program Files/Python310/python.exe"
    pause
    exit /b 1
)

set "VENV_DIR=%~dp0.venv"
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment at %VENV_DIR% ...
    %PYEXE% -m venv "%VENV_DIR%"
    if errorlevel 1 ( echo [ERROR] venv creation failed. & pause & exit /b 1 )
) else (
    echo Reusing existing virtual environment at %VENV_DIR%
)

set "VPY=%VENV_DIR%\Scripts\python.exe"

echo Upgrading pip / setuptools / wheel ...
"%VPY%" -m pip install %PROXY_ARG% --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [ERROR] Could not upgrade pip. If you are behind a corporate proxy,
    echo edit this file and set PIP_PROXY=http://your-proxy-host:port
    pause
    exit /b 1
)

echo Installing dependencies (this can take a few minutes) ...
"%VPY%" -m pip install %PROXY_ARG% -r "%~dp0requirements.txt"
if errorlevel 1 ( echo [ERROR] dependency install failed. & pause & exit /b 1 )

echo.
echo === Setup complete. Launch with run-viewline.bat ===
echo.
pause
endlocal
