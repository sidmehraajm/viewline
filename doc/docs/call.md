### Running Viewline

Viewline is a standalone Python application that can be launched directly from the command line or through a platform-specific launcher script.

### Requirements

Before running Viewline, ensure the following are installed:

* Python 3.10 or newer
* PySide6
* PyAV
* NumPy
* OpenImageIO
* OpenColorIO
* PyOpenGL
* OpenUSD
* All additional Python dependencies listed in the development kit

---

### OpenUSD

Viewline requires **OpenUSD 26.05**.

<p style="text-align: justify;">
Since prebuilt binaries may not be available for every platform, it is recommended to build <strong>OpenUSD 26.05</strong> from source.
</p>

### Build OpenUSD 26.05

Follow the official OpenUSD build instructions to compile the library for your platform.

<https://github.com/PixarAnimationStudios/OpenUSD/releases/tag/v26.05>

After building OpenUSD, ensure that:

- The OpenUSD Python bindings are available.
- The required OpenUSD libraries are accessible through your system environment.
- Viewline can locate the OpenUSD installation.

---

### OpenColorIO

The OpenColorIO configuration file (`config.ocio`) must be available before launching Viewline.

Set the `OCIO` environment variable to point to your configuration file if it is not configured automatically.

---

### Download latest version

<p>
    <a href="https://github.com/subing85/viewline/releases" download>
        📥 Viewline 
    </a>
</p>


### Windows

Create a launcher batch file (`viewline.bat`) similar to the following.

```bat

:: Viewline source directory

set "VIEWLINE_SOURCE=D:/developments"

:: Python installation
set "PYTHON=C:/Program Files/Python310/python.exe"

:: Third-party libraries
set "LIB_DIR=D:/developments/devkit/site-packages"

:: OpenUsd directory
set "USD_PLUGIN_PATH=D:/developments/devkit/plug-ins/OpenUSD-26.05"

:: Append the PATH to usd plugin path
set "PATH=%PATH%;%USD_PLUGIN_PATH%/bin;%USD_PLUGIN_PATH%/lib"

:: Python search path
set "PYTHONPATH=%VIEWLINE_SOURCE%LIB_DIR%/charset-normalizer/3.3.2;%LIB_DIR%/certifi/2024.2.2;%LIB_DIR%/idna/3.7;%LIB_DIR%/urllib3/2.2.1;%LIB_DIR%/requests/2.32.2;%LIB_DIR%/darkdetect/0.7.1;%LIB_DIR%/pyqtdarktheme/2.1.0;%LIB_DIR%/OpenImageIO/3.0.4.0;%LIB_DIR%/PySide6/6.9.0;%LIB_DIR%/shiboken6/6.9.0;%LIB_DIR%/PySide6-Essentials/6.9.0;%LIB_DIR%/PySide6-Addons/6.9.0;%LIB_DIR%/PyOpenGL/3.1.9;%LIB_DIR%/opencolorio/2.5.0;%LIB_DIR%/av/17.0.0;%LIB_DIR%/numpy/1.26.4;%USD_PLUGIN_PATH%/lib/python;"

:: OpenColorIO configuration
set "OCIO=D:/developments/devkit/ocio/studio-config-v4.0.0_aces-v2.0_ocio-v2.5.ocio"

:: User profile
set "VIEW_LINE_PROFILE_ROOT=%USERPROFILE%/Documents"

:: Launch Viewline
"%PYTHON%" "%VIEWLINE_SOURCE%/viewline/main.py" %*

```

Run the application by double-clicking the batch file or from a command prompt.

---

### Linux

Create a launcher shell script (`viewline.sh`).

```bash
#!/bin/bash

# Viewline source directory
export VIEWLINE_SOURCE=D:/developments/

# Python installation
export PYTHON=/usr/bin/python3.10

# Third-party libraries
export LIB_DIR=/developments/devkit/site-packages

# OpenUsd directory
export USD_PLUGIN_PATH=/developments/devkit/plug-ins/OpenUSD-26.05

# Append the PATH to usd plugin path
export PATH=$PATH;$USD_PLUGIN_PATH/bin;$USD_PLUGIN_PATH/lib"

# Python search path
export PYTHONPATH=\
$VIEWLINE_SOURCE:\
$LIB_DIR/charset-normalizer/3.3.2:\
$LIB_DIR/certifi/2024.2.2:\
$LIB_DIR/idna/3.7:\
$LIB_DIR/urllib3/2.2.1:\
$LIB_DIR/requests/2.32.2:\
$LIB_DIR/darkdetect/0.7.1:\
$LIB_DIR/pyqtdarktheme/2.1.0:\
$LIB_DIR/OpenImageIO/3.0.4.0:\
$LIB_DIR/PySide6/6.9.0:\
$LIB_DIR/shiboken6/6.9.0:\
$LIB_DIR/PySide6-Essentials/6.9.0:\
$LIB_DIR/PySide6-Addons/6.9.0:\
$LIB_DIR/PyOpenGL/3.1.9:\
$LIB_DIR/opencolorio/2.5.0:\
$LIB_DIR/av/17.0.0:\
$LIB_DIR/numpy/1.26.4:\
$USD_PLUGIN_PATH//lib/python:\

# OpenColorIO configuration
export OCIO=/developments/devkit/ocio/studio-config-v4.0.0_aces-v2.0_ocio-v2.5.ocio

# User profile
export VIEW_LINE_PROFILE_ROOT=$HOME/Documents

# Launch Viewline
"$PYTHON" "%VIEWLINE_SOURCE%/viewline/main.py" "$@"


```

Make the launcher executable.

```bash
chmod +x viewline.sh
```

Run the application.

```bash
./viewline.sh
```

---

### Environment Variables

| Variable                 | Description                                                                                   |
| ------------------------ | --------------------------------------------------------------------------------------------- |
| `PYTHON`                 | Python executable used to launch Viewline.                                                    |
| `PYTHONPATH`             | Locations of all required third-party Python packages and the Viewline source directory.      |
| `OCIO`                   | Path to the OpenColorIO configuration file.                                                   |
| `VIEW_LINE_PROFILE_ROOT` | Directory used by Viewline to store user preferences, recent files, and application settings. |
| `PATH`                   |  Append the PATH to usd plugin lib and bin path.                                              |

---

### Customizing Your Studio Environment

The launcher scripts included above are reference implementations.

<p style="text-align: justify;">Every studio has a different pipeline structure, Python installation, development kit, and OpenColorIO configuration. Before deploying Viewline, update the following values to match your production environment:</p>

* Python executable
* Third-party library locations
* Viewline installation directory
* OpenColorIO configuration
* User profile directory
* OpenUSD 26.05

<p style="text-align: justify;">Only these paths need to be changed. The application itself requires no source code modifications to run in a different studio environment.</p>

---

**© Support, subing85@gmail.com.**

---
