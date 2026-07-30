"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./utils/__init__.py

Description:
    This module provides common helper utilities used throughout the Review Player framework.

Responsibilities:
    - File/path utilities
    - URL handling
    - Sequence discovery
    - Resource downloading
    - Watermark data processing
    - Path construction helpers

Features:
    - File extension utilities
    - URL validation
    - Sequence pattern resolution
    - Web browser launching
    - Remote image downloading
    - Watermark override generation

Architecture:
    Input Data
        ↓
    Utility Processing
        ↓
    Resolved Output

Notes:
    This module contains reusable utility functions
    shared across:
        - Playback
        - Viewer
        - Playlist
        - Resources
        - Watermark systems
"""

from __future__ import absolute_import

import os
import re
import json
import glob
import uuid
import shutil
import base64
import urllib
import getpass
import datetime
import requests
import tempfile
import platform
import webbrowser
import subprocess

from viewline import logger
from viewline import resources
from viewline import constants

LOGGER = logger.getLogger(__name__)


def getPlatform():
    """Return the current operating system.

    Returns:
        str:
            Lowercase platform name.

            Supported values include::

                "windows"
                "linux"
    """

    # Convert platform name to lowercase for consistency.
    return platform.system().lower()


def getUsername():
    """Return the current system username.

    Returns:
        str:
            Username of the currently logged-in user.
    """

    # Query the operating system for the active user.
    return getpass.getuser()


def hasPathExists(filepath):
    """Check whether path exists.

    Environment variables are automatically expanded.

    Args:
        filepath (str):
            File or directory path.

    Returns:
        bool | None:
            True if path exists,
            False if path does not exist,
            None if filepath is invalid.

    Example:
        >>> hasPathExists("/tmp/test.exr")
        >>> hasPathExists("$HOME/test.mov")
    """

    # Validate Input
    if not filepath:
        return None

    # Expand Environment Variables
    absfilepath = os.path.expandvars(filepath)

    # Check Path Exists
    return os.path.exists(absfilepath)


def fileName(filepath, extension=False):
    """
    Return the file name from a file path.

    Args:
        filepath (str):
            Absolute or relative file path.

        extension (bool, optional):
            Include file extension in the returned name.
            Defaults to False.

    Returns:
        str:
            File name with or without extension.

    Examples:
        >>> fileName("/tmp/image.png")
        'image'

        >>> fileName("/tmp/image.png", extension=True)
        'image.png'
    """

    # Extract file name from path
    basename = os.path.basename(filepath)

    # Return with extension
    if extension:
        name = basename

    # Return without extension
    else:
        name = os.path.splitext(basename)[0]

    return name


def fileExtension(filepath, dot=False):
    """Return lowercase file extension.

    Args:
        filepath (str):
            File path.

    Returns:
        str:
            Lowercase file extension.

    Example:
        >>> fileExtension("/tmp/test.EXR")
        '.exr'
    """

    # Extract File Extension
    # return os.path.splitext(filepath)[1].lower()

    splitext = os.path.splitext(filepath)[-1]

    if dot:
        result = splitext.lower()
    else:
        result = splitext.rsplit(".", 1)[-1].lower()

    return result


def dirname(path):
    """Return directory name from path.

    Args:
        path (str):
            File path.

    Returns:
        str:
            Directory path.

    Example:
        >>> dirname("/tmp/test.exr")
        '/tmp'
    """

    # Extract Directory Name
    return os.path.dirname(path)


def pathResolver(path, folders=list(), filename=None):
    """Build path from folders and filename.

    Args:
        path (str):
            Root path.

        folders (list):
            Folder list.

        filename (str | None):
            Optional filename.

    Returns:
        str:
            Resolved file path.

    Example:
        >>> pathResolver("/tmp", ["images", "renders"], "test.exr")
    """

    # Build Path with Expand Environment Variables
    if filename:
        result = os.path.expandvars(os.path.join(path, *folders, filename)).replace("\\", "/")
    else:
        result = os.path.expandvars(os.path.join(path, *folders)).replace("\\", "/")

    return result


def openPath(path):
    """Open a file or directory using the operating system.

    This function launches the default file manager or associated application for the given path.

    Args:
        path (str):
            File or directory to open.
    """

    # Validate that the target exists.
    if not hasPathExists(path):
        LOGGER.warning(f"Could not found such path, {path}")
        return

    # Detect the current operating system.
    operatingSystem = getPlatform()

    # Windows uses the "start" shell command.
    if operatingSystem == "windows":
        subprocess.Popen(["start", path], shell=True)

    # Linux uses xdg-open.
    if operatingSystem == "linux":
        subprocess.Popen(["xdg-open", path])


def openUrl(path):
    """Open URL in default browser.

    Args:
        path (str):
            URL address.

    Example:
        >>> openUrl("https://github.com")
    """

    # Open URL
    webbrowser.open(path)


def isUrl(path):
    """Check whether path is a URL.

    Args:
        path (str):
            File path or URL.

    Returns:
        bool:
            True if valid HTTP/HTTPS URL.

    Example:
        >>> isUrl("https://github.com")
        True

        >>> isUrl("/tmp/test.exr")
        False
    """

    # Parse URL
    result = urllib.parse.urlparse(path)

    # Validate URL Scheme
    return result.scheme in ("http", "https")


def getUrlContent(url, encode=False):
    """Download URL content.

    Args:
        url (str):
            URL address.

        encode (bool):
            Return Base64 encoded content.

    Returns:
        bytes | str | None:
            Raw bytes,
            Base64 encoded string,
            or None.

    Example:
        >>> content = getUrlContent(url)
        >>> encoded = getUrlContent(url, encode=True)
    """

    # Validate URL
    if not url:
        return

    # Download URL Content
    content = requests.get(url).content

    # Return Raw Content
    if not encode:
        return content

    # Encode Base64 Content
    encoded = base64.b64encode(content).decode()

    return encoded


def getSequence(path):
    """Return image sequence files.

    Converts sequence pattern hashes into glob patterns.

    Example:
        image.####.exr
            ↓
        image.*.exr

    Args:
        path (str):
            Sequence pattern.

    Returns:
        list:
            Sorted sequence files.

    Example:
        >>> getSequence("/show/render/image.####.exr")
    """

    # Convert Hash Pattern To Glob Pattern
    pattern = re.sub(r"#+", "*", path)

    # Search Sequence Files
    files = sorted(glob.glob(pattern))

    return files


def overrideWatermarkValues(version, watermarks=None, **kwargs):
    """Override watermark values from version data.

    This function injects dynamic values into watermark overlay presets.

    Supported Dynamic Values:
        - Project name
        - Shot name
        - Task name
        - Artist name
        - Date
        - Copyright
        - Project logo
        - Studio logo

    Args:
        version (dict):
            Version/media dictionary.

        watermarks (dict | None):
            Watermark preset data.

        **kwargs:
            Additional override values.

    Keyword Args:
        studio_logo (str):
            Studio logo path or URL.

        project_logo (str):
            Project logo path or URL.

    Returns:
        dict:
            Updated watermark data.

    Example:
        >>> overlays = overrideWatermarkValues(
        ...     version,
        ...     studio_logo="/tmp/logo.png"
        ... )
    """

    # Load Default Watermark Preset
    watermarks = watermarks or resources.getPreset("watermarks")

    # Iterate Watermark Positions
    for position in watermarks:
        # Iterate Overlay Items
        for overlay in watermarks[position]:
            # Skip Disabled Overlay
            if not overlay.get("enable"):
                continue

            # Validate Overlay Code
            code = overlay.get("code")
            if not code:
                continue

            # Copyright Label
            if code == "copyright":
                overlay["value"] = constants.COPYRIGHT_LABEL
                continue

            # Studio Logo
            if code == "studio-logo":
                overlay["value"] = kwargs.get("studio_logo")
                continue

            # Project Logo
            if code == "project-logo":
                overlay["value"] = kwargs.get("project_logo")
                continue

            # Resolve Version Value
            value = version.get(code)

            # Store Empty Value
            if value is None:
                overlay["value"] = value
                continue

            # Entity Dictionary Support
            if isinstance(value, dict):
                value = value.get("name") or value.get("code") or ""

            # Store Override Value
            overlay["value"] = value

    return watermarks


def getDateTimes(times=None):
    """Return a formatted date and time string.

    Args:
        times (datetime.datetime, str, optional):
            Datetime object to format.

            If None, the current date and time are used.

            If a string is supplied, it is returned unchanged.

    Returns:
        str:
            Formatted date/time string.
    """

    # Preserve existing formatted strings.
    if isinstance(times, str):
        return times

    # Use the supplied time or the current time.
    now = times if times else datetime.datetime.now()

    # Format using the project date format.
    result = now.strftime(constants.DATE_TIME_FORMAT)
    return result


def getTempDate(context=None):
    """Return a timestamp suitable for temporary names.

    The generated string is commonly used for creating unique temporary folders and files.

    Args:
        context (datetime.datetime, optional):
            Datetime object to format.

            If None, the current date and time is used.

    Returns:
        str:
            Timestamp formatted for temporary resources.
    """

    # Use the supplied time or the current time.
    now = context if context else datetime.datetime.now()

    # Format into a readable unique timestamp.
    date_time = now.strftime("%Y-%B-%d-%A-%I-%M-%S-%p")

    return date_time


def tempdir(subfolder=False):
    """Return the system temporary directory.

    Optionally creates a unique timestamp-based subdirectory path.

    Args:
        subfolder (bool):
            Create a unique temporary subfolder.

    Returns:
        str:
            Temporary directory path.
    """

    # Resolve the operating system temporary directory.
    directory = pathResolver(tempfile.gettempdir())

    # Append a timestamp folder when requested.
    if subfolder:
        directory = pathResolver(directory, folders=[getTempDate()])

    return directory


def hasFile(filepath):
    """Determine whether a path contains a filename.

    Args:
        filepath (str):
            File or directory path.

    Returns:
        bool:
            True if the path contains a file extension,
            otherwise False.
    """

    # Split the path into filename and extension.
    dirname, extenstion = os.path.splitext(filepath)

    # A path with an extension is treated as a file.
    return True if extenstion else False


def jsonDefaultSerializer(obj):
    """Serialize unsupported objects for JSON encoding.

    This serializer extends the default JSON encoder by converting application-specific objects into JSON-compatible values.

    Supported object types:
        - datetime.date
        - datetime.datetime
        - QTreeWidgetItem

    Args:
        obj (object):
            Object to serialize.

    Returns:
        object:
            JSON-compatible representation.

    Raises:
        TypeError:
            If the object type is not supported.
    """

    # Convert date and datetime objects into project date format.
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.strftime(constants.DATE_TIME_FORMAT)

    # Unsupported object type.
    raise TypeError(f"Type {type(obj)} not serializable")


def writeJsonFile(context, filepath, serializer=False, indent=4):
    """Write data to a JSON file.

    Creates parent directories automatically before writing.

    Args:
        context (dict):
            Data to write.

        filepath (str):
            Destination JSON file.

        serializer (bool):
            Enable the custom JSON serializer.

        indent (int):
            JSON indentation level.
    """

    # Ensure the destination directory exists.
    makedirs(filepath)

    # Enable the custom serializer when requested.
    default = jsonDefaultSerializer if serializer else None

    # Write formatted JSON to disk.
    with open(filepath, "w") as target:
        target.write(json.dumps(context, default=default, indent=indent))


def readJsonFile(filepath):
    """Read a JSON file.

    Note:
        This function is deprecated and scheduled for removal.

    Args:
        filepath (str):
            JSON file path.

    Returns:
        dict or list or None:
            Parsed JSON data if the file exists.
    """

    # Return if the file does not exist.
    if not hasPathExists(filepath):
        return

    # Load and parse the JSON file.
    with open(filepath, "r") as target:
        return json.load(target)


def makedirs(path, open=False):
    """Create directories if they do not already exist.

    If a file path is supplied, only its parent directory is created.

    Args:
        path (str):
            Directory or file path.

        open (bool):
            Open the directory after creation.
    """

    # Ignore empty paths.
    if not path:
        return

    # Expand environment variables.
    abspath = os.path.expandvars(path)

    # Convert file paths into their parent directory.
    if hasFile(abspath):
        abspath = os.path.dirname(abspath)

    # Create the directory when required.
    if not os.path.isdir(abspath):
        os.makedirs(abspath, exist_ok=True)

    # Open the directory if requested.
    if open:
        openPath(abspath)


def getStatusFieldValue(value):
    """Return the status code for a status value.

    Searches the project status list and returns the matching status code.

    Args:
        value (str):
            Status value.

    Returns:
        str or None:
            Matching status code or the original value if
            no match exists.
    """

    # Ignore empty values.
    if not value:
        return

    # Find the matching status entry.
    current_status = next(filter(lambda x: x["value"] == value, constants.STATUS_LIST), None)

    # Return the status code when available.
    result = current_status["code"] if current_status else value

    return result


def environmentValue(key):
    """Return an environment variable.

    Args:
        key (str):
            Environment variable name.

    Returns:
        str or None:
            Environment variable value.
    """

    # Read the environment variable.
    return os.getenv(key)


def viewlinePath(subfolder=None):
    """Return the Viewline profile directory.

    The path is resolved from the VIEW_LINE_PROFILE_ROOT environment variable.

    Args:
        subfolder (str, optional):
            Additional folder inside the Viewline profile.

    Returns:
        str:
            Resolved Viewline profile path.
    """

    # Build the Viewline profile path.
    result = pathResolver(
        environmentValue("VIEW_LINE_PROFILE_ROOT"), folders=["viewline", subfolder]
    )

    return result


def numericId():
    """Generate a unique numeric identifier.

    The identifier is derived from a UUID time component and is suitable for temporary filenames and resource identifiers.

    Returns:
        int:
            Unique numeric identifier.
    """

    # Generate a time-based UUID.
    id = uuid.uuid1()

    # Return the numeric time component.
    return int(id.time_low)


def copyFile(source, destination, delete=False):
    """Copy a file to a new location.

    Creates the destination directory automatically before copying.
    If the source and destination resolve to the same location,
    no copy is performed.

    Args:
        source (str):
            Source file path.

        destination (str):
            Destination file path.

        delete (bool):
            Reserved for future support to remove the source file
            after copying.

    Returns:
        str:
            Absolute path of the copied file.
    """

    # Ensure the destination directory exists.
    makedirs(destination)

    # Skip copying when both paths are identical.
    if pathResolver(source) == pathResolver(destination):
        return pathResolver(source)

    # Copy the file while preserving metadata.
    copiedFile = shutil.copy2(source, destination)

    # Return the normalized destination path.
    return pathResolver(copiedFile)


def redirectPreset(preset, target):
    """Redirect preset resources to a target directory.

    Copies all preset resources into the specified directory and
    updates the preset context to reference the newly created files.

    Supported resource types:
        - USD files
        - Images
        - Movie files
        - Image sequences

    Args:
        preset (str):
            Preset resource name.

        target (str):
            Destination directory.

    Returns:
        list[dict]:
            Updated preset context list.
    """

    # Load preset definition.
    context_list = resources.getPreset(preset)

    # Process every preset entry.
    for context in context_list:

        # ------------------------------------------------------------------
        # Redirect USD files.
        # ------------------------------------------------------------------
        if context.get("usd"):

            # Generate a unique filename.
            numid = numericId()
            extension = fileExtension(context["usd"])

            # Resolve source and destination paths.
            folder = dirname(context["usd"])

            source = pathResolver(resources.CURRENT_PATH, filename=context["usd"])
            destination = pathResolver(target, folders=[folder], filename=f"{numid}.{extension}")

            # Update the preset reference.
            context["usd"] = f"{folder}/{numid}.{extension}"

            # Copy the resource.
            copyFile(source, destination)

        # ------------------------------------------------------------------
        # Redirect image files.
        # ------------------------------------------------------------------
        if context.get("image"):
            numid = numericId()
            extension = fileExtension(context["image"])

            folder = dirname(context["image"])

            source = pathResolver(resources.CURRENT_PATH, filename=context["image"])
            destination = pathResolver(target, folders=[folder], filename=f"{numid}.{extension}")

            # Update the preset reference.
            context["image"] = f"{folder}/{numid}.{extension}"

            # Copy the resource.
            copyFile(source, destination)

        # ------------------------------------------------------------------
        # Redirect media files.
        # ------------------------------------------------------------------
        if context.get("media"):

            # Resolve the original media path.
            filepath = pathResolver(resources.CURRENT_PATH, filename=context["media"])

            # Detect movie or image sequence.
            files = getSequence(filepath)

            if not files:
                continue

            # Generate a unique identifier.
            numid = numericId()
            folder = dirname(context["media"])
            base_name = fileName(context["media"])
            extension = fileExtension(context["media"])

            # --------------------------------------------------------------
            # Image sequence.
            # --------------------------------------------------------------
            if len(files) > 1:

                # Extract sequence padding (####).
                name_parts = base_name.rsplit(".", 1)
                padding = name_parts[1] if len(name_parts) > 1 else "####"  # e.g., "####"

                # Update the sequence pattern.
                context["media"] = f"{folder}/{numid}.{padding}.{extension}"

                # Copy every frame.
                for file in files:
                    # Assuming individual files in the sequence have actual frame numbers,
                    # we extract the frame number from the current file name to keep them unique
                    actual_frame = fileName(file).rsplit(".", 2)[1]  # Extracts the frame number

                    new_filename = f"{numid}.{actual_frame}.{extension}"
                    destination = pathResolver(target, folders=[folder], filename=new_filename)
                    copyFile(file, destination)

            # --------------------------------------------------------------
            # Single media file.
            # --------------------------------------------------------------
            else:
                # For single files (e.g., .mp4)
                file = files[0]
                new_filename = f"{numid}.{extension}"

                # Update the preset reference.
                context["media"] = f"{folder}/{new_filename}"
                destination = pathResolver(target, folders=[folder], filename=new_filename)

                # Copy the media file.
                copyFile(file, destination)

    return context_list


def getSourceFile(context):
    """Return the available source type.

    Determines whether a preset references a USD scene or a media file.

    Args:
        context (dict):
            Preset context.

    Returns:
        str:
            Either ``"usd"`` or ``"media"``.

    Raises:
        ValueError:
            If neither source exists.
    """

    # Retrieve source entries.
    usd = context.get("usd")
    media = context.get("media")

    # Invalid configuration.
    if usd and media:
        return None

    # USD source.
    if usd:
        return "usd"

    # Media source.
    if media:
        return "media"

    # No supported source found.
    raise ValueError("Neither 'usd' nor 'media' found in context.")


def getSourceCategory(filepath):
    """Return the Viewline source category.

    Determines whether the supplied file is a supported USD scene or media file based on its extension.

    Args:
        filepath (str):
            File path.

    Returns:
        str or None:
            One of:

                - "usd"
                - "media"
                - None
    """

    # Extract the file extension.
    extension = fileExtension(filepath, dot=False)

    # Check for supported USD formats.
    if extension in constants.USD_EXTENSIONS:
        result = "usd"

    # Check for supported media formats.
    elif extension in constants.MEDIA_EXTENSIONS:
        result = "media"

    # Unsupported file type.
    else:
        result = None

    return result


if __name__ == "__main__":
    pass
