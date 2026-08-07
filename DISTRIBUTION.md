# Distributing Viewline (no install on target PCs)

Goal: give teammates a folder (or single exe) they can run without installing
Python, USD, OpenImageIO, or anything else. Everything is bundled.

## Recommended: PyInstaller onedir (a self-contained folder)

This produces `dist\Viewline\` containing `Viewline.exe` plus every DLL and
dependency. Copy the folder to any Windows PC and run the exe. Nothing to
install.

**Build steps (on your dev machine):**

1. Make sure the app runs from source first (`run-viewline.bat` works).
2. Double-click **`build-exe.bat`**. It installs PyInstaller into the venv and
   runs `viewline.spec`. Takes a few minutes.
3. Result: **`dist\Viewline\Viewline.exe`**.
4. Zip the whole `dist\Viewline` folder and share it. Teammates unzip and run
   `Viewline.exe`.

**Why onedir and not a single .exe?** USD, OpenImageIO and OpenColorIO are large
native libraries. A single-file exe has to unpack them to a temp dir on every
launch (slow, and occasionally trips antivirus). The onedir folder starts fast
and is far more reliable. If you still want one file, change the spec to a
`onefile` EXE — ask and I'll adjust it.

**First-build gotchas (native libs):** the spec already pulls in `pxr` (USD),
`OpenImageIO`, `PyOpenColorIO`, `av`, `numpy`, and `ayon_api` via
`collect_all`. If a teammate hits a `ModuleNotFoundError` or a missing-DLL error
on the target PC:
- note the missing module/DLL name,
- add it to `hiddenimports` (or its package to the `collect_all` list) in
  `viewline.spec`, and rebuild.
This is normal iteration for apps with heavy native deps; usually 0–2 additions.

Since your workflow is images + movies (USD 3D viewport is optional and
guarded), even if some USD imaging resources don't bundle, playback still works.

## What the users need to do

- Nothing to install. Run `Viewline.exe`.
- On first launch they get the **login dialog** (server + AYON username +
  password). With **Remember me** checked, subsequent launches auto-login.
- The server defaults to `http://ayon:5000`; they can change it. They must be
  able to reach that server on their network and have the mounted media drive
  (e.g. `P:\`) available, since media is read from local/mounted storage.

## Config that ships with the build

- The AYON server/API-key env vars in `run-viewline.bat` are **no longer
  required** for the exe — login provides the session. (Keep the bat only for
  running from source.)
- If you want the exe to point at a fixed server by default, set it in the login
  dialog's placeholder or pre-seed it; tell me and I'll bake in a default.

## Alternative (not recommended): ship the venv folder

Copying the repo + `.venv` + a launcher seems easy, but a Windows venv still
references the base Python install for its standard library, so it breaks on a
PC without matching Python. PyInstaller (above) bundles a real Python and is the
correct "no-install" path.

## Updating

To ship a new version: rebuild with `build-exe.bat`, re-zip `dist\Viewline`,
and distribute. Users replace their old folder.
