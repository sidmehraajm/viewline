:: Viewline launcher (venv-based, images + movies, no USD)
:: Run setup-viewline.bat once before using this.

@echo off
setlocal

set "REPO_DIR=%~dp0"
:: Strip trailing backslash
if "%REPO_DIR:~-1%"=="\" set "REPO_DIR=%REPO_DIR:~0,-1%"

:: Parent of the repo folder must be importable (code uses "from viewline import ...")
for %%I in ("%REPO_DIR%") do set "PARENT_DIR=%%~dpI"
if "%PARENT_DIR:~-1%"=="\" set "PARENT_DIR=%PARENT_DIR:~0,-1%"

set "VENV_PY=%REPO_DIR%\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo [ERROR] venv not found. Run setup-viewline.bat first.
    pause
    exit /b 1
)

:: --- Required: Viewline profile / working directory ---
set "VIEW_LINE_PROFILE_ROOT=%USERPROFILE%\Documents"

:: --- Make the "viewline" package importable ---
set "PYTHONPATH=%PARENT_DIR%;%PYTHONPATH%"

:: --- Optional: OCIO / ACES color config. Uncomment and point to a .ocio file. ---
:: set "OCIO=C:\ocio\studio-config-v4.0.0_aces-v2.0_ocio-v2.5.ocio"

:: --- AYON integration ---
set "VIEWLINE_BACKEND=ayon"
set "AYON_SERVER_URL=http://ayon:5000"
set "AYON_API_KEY=c8e65fba4bfc4de1a5021656680776d0"

:: Optional: only show these product types (comma list). Empty = any with media.
:: set "VIEWLINE_AYON_PRODUCT_TYPES=render,review,plate"

:: Optional: manual root mapping if media paths keep {root[...]} tokens
:: (JSON on ONE line). Point these at your mounted studio storage.
:: set "VIEWLINE_AYON_ROOTS={\"work\": \"P:/projects\"}"

:: Optional: AYON site id used for root resolution
:: set "AYON_SITE_ID=your-site-id"

"%VENV_PY%" "%REPO_DIR%\main.py" %*

endlocal
