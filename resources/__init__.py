"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./resources/__init__.py

Description:
    This module provides centralized access to project resource files used throughout the Review Player framework.

Responsibilities:
    - Icon path resolution
    - Preset file loading
    - JSON resource reading

Supported Resources:
    - Icons
    - Presets
    - JSON configuration files

Directory Structure:
    resources/
        icons/
        presets/

Presets:
    - projects.json
    - versions.json
    - watermarks.json

Architecture:
    Resource Name
        ↓
    Resource Resolver
        ↓
    Absolute File Path
        ↓
    JSON/File Loading

Notes:
    This module acts as the central resource access layer for the application.
"""

from __future__ import absolute_import

import os
import json

# Current Resource Directory
CURRENT_PATH = os.path.dirname(__file__)


def getIconFilepath(name):
    """Return icon file path.

    Resolves icon resource paths from:
        resources/icons/

    Args:
        name (str):
            Icon file name without extension.

    Returns:
        str:
            Absolute icon file path.

    Example:
        >>> path = getIconFilepath("play")

        >>> path = getIconFilepath("mc-review-player")
    """

    # Build Icon File Path
    filepath = os.path.abspath(os.path.join(CURRENT_PATH, "icons", f"{name}.png"))

    return filepath


def getPreset(name):
    """Return preset JSON data.

    Loads preset files from:
        resources/presets/

    Args:
        name (str):
            Preset name without extension.

    Returns:
        dict | list:
            Parsed JSON preset data.

    Supported Presets:
        - projects
        - versions
        - watermarks

    Example:
        >>> projects = getPreset("projects")
        >>> versions = getPreset("versions")
    """

    # Build Preset File Path
    filepath = os.path.abspath(os.path.join(CURRENT_PATH, "presets", f"{name}.json"))

    # Read JSON Preset File
    result = readJsonFile(filepath)

    return result


def readJsonFile(filepath):
    """Read JSON file content.

    Args:
        filepath (str):
            JSON file path.

    Returns:
        dict | list:
            Parsed JSON content.

    Example:
        >>> data = readJsonFile("/tmp/test.json")
    """

    # Open JSON File
    with open(filepath, "r") as target:
        # Parse JSON Content
        content = json.load(target)
        return content


def readShader(name):
    """Read a complete OpenGL shader program.

    Loads both the vertex shader and fragment shader associated with the specified shader name.

    Expected Files:
        materials/<name>.vert
        materials/<name>.frag

    Args:
        name (str):
            Shader program name without file extension.

    Returns:
        tuple[str, str]:
            Vertex shader source followed by fragment shader source.
    """

    # Resolve the vertex shader file.
    vertex_path = os.path.abspath(os.path.join(CURRENT_PATH, "materials", f"{name}.vert"))

    # Read the vertex shader source.
    with open(vertex_path, "r", encoding="utf-8") as stream:
        vertex_source = stream.read()

    # Resolve the fragment shader file.
    fragment_path = os.path.abspath(os.path.join(CURRENT_PATH, "materials", f"{name}.frag"))

    # Read the fragment shader source.
    with open(fragment_path, "r", encoding="utf-8") as stream:
        fragment_source = stream.read()

    # Return both shader sources.
    return vertex_source, fragment_source


def readVertexShader(name):
    """Read a vertex shader source file.

    Loads only the vertex shader associated with the specified shader
    name.

    Expected File:
        materials/<name>.vert

    Args:
        name (str):
            Vertex shader name without file extension.

    Returns:
        str:
            Vertex shader source code.
    """

    # Resolve the vertex shader file.
    vertex_path = os.path.abspath(os.path.join(CURRENT_PATH, "materials", f"{name}.vert"))

    # Read the vertex shader source.
    with open(vertex_path, "r", encoding="utf-8") as stream:
        vertex_source = stream.read()

    # Return the shader source.
    return vertex_source


if __name__ == "__main__":
    pass
