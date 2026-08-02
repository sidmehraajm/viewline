"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./widgets/pixmaps.py

Description:
    This module provides reusable Qt pixmap and icon wrapper classes used throughout the Review Player UI.

Responsibilities:
    - Load pixmaps from resources
    - Load pixmaps from URLs
    - Create reusable Qt icons
    - Provide fallback placeholder icons
    - Simplify icon/pixmap creation

Features:
    - Resource icon loading
    - URL image loading
    - Local image loading
    - Automatic fallback icons
    - QPixmap wrappers
    - QIcon wrappers

Architecture:
    Image Source
        ↓
    Pixmap Wrapper
        ↓
    Icon Generation
        ↓
    Qt Widgets/UI

Supported Sources:
    - Resource icons
    - Local file paths
    - HTTP/HTTPS URLs

Notes:
    This module is used by:
        - Playlist widgets
        - Buttons
        - Menus
        - Tree widgets
        - Viewer overlays
"""

from __future__ import absolute_import

from PySide6 import QtGui

from viewline import utils
from viewline import resources


class NamePixmap(QtGui.QPixmap):
    """Pixmap wrapper using resource icon names.

    This class automatically resolves icon names from
    the Review Player resources/icons directory.

    Features:
        - Resource icon lookup
        - Automatic fallback icons
        - QPixmap loading

    Args:
        name (str):
            Icon name without extension.

    Example:
        >>> pixmap = NamePixmap("play")
        >>> pixmap = NamePixmap("unknown")
    """

    def __init__(self, name, **kwargs):
        """Initialize named pixmap.

        Args:
            name (str):
                Resource icon name.

            **kwargs:
                Reserved for future extension.
        """

        # Initialize QPixmap
        super(NamePixmap, self).__init__()

        # Resolve Resource File Path
        self.filepath = resources.getIconFilepath(name)

        # Fallback To Unknown Icon
        if not utils.hasPathExists(self.filepath):
            self.filepath = resources.getIconFilepath("unknown")

        # Load Pixmap
        self.load(self.filepath)


class NamePixmapIcon(QtGui.QIcon):
    """QIcon wrapper using resource icon names.

    This class creates a Qt icon from a named
    Review Player resource icon.

    Features:
        - Resource icon lookup
        - Automatic pixmap conversion
        - QIcon creation

    Args:
        name (str):
            Resource icon name.

    Example:
        >>> icon = NamePixmapIcon("play")
    """

    def __init__(self, name, **kwargs):
        """Initialize named icon.

        Args:
            name (str):
                Resource icon name.

            **kwargs:
                Reserved for future extension.
        """

        # Initialize QIcon
        super(NamePixmapIcon, self).__init__()

        # Build Pixmap
        pixmap = NamePixmap(name)

        # Add Pixmap To Icon
        self.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)


class PixmapIcon(QtGui.QIcon):
    """QIcon wrapper from existing pixmap.

    This helper converts an existing QPixmap into
    a reusable Qt icon.

    Args:
        pixmap (QPixmap):
            Source pixmap.

    Example:
        >>> icon = PixmapIcon(pixmap)
    """

    def __init__(self, pixmap, **kwargs):
        """Initialize pixmap icon.

        Args:
            pixmap (QPixmap):
                Source pixmap.

            **kwargs:
                Reserved for future extension.
        """

        # Initialize QIcon
        super(PixmapIcon, self).__init__()

        # Add Pixmap To Icon
        self.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)


class PathPixmap(QtGui.QPixmap):
    """Pixmap wrapper for local files and URLs.

    Supports:
        - Local image paths
        - HTTP/HTTPS image URLs

    Features:
        - Automatic URL detection
        - Remote image downloading
        - Local file loading

    Args:
        filepath (str):
            Local path or URL.

    Example:
        >>> pixmap = PathPixmap("/tmp/image.png")
        >>> pixmap = PathPixmap("https://server/image.jpg")
    """

    def __init__(self, filepath, **kwargs):
        """Initialize path pixmap.

        Args:
            filepath (str):
                Local image path or URL.

            **kwargs:
                Reserved for future extension.
        """

        # Initialize QPixmap
        super(PathPixmap, self).__init__()

        if utils.isUrl(filepath):  # Load Remote Image
            self.loadFromData(utils.getUrlContent(filepath))
        else:  # Load Local Image
            self.load(filepath)


class ImageDataPixmap(QtGui.QPixmap):
    """Pixmap created from a NumPy image.

    This class converts a NumPy image array into a Qt ``QPixmap`` for display inside Qt widgets.
    Both RGB and RGBA image formats are supported.

    Attributes:
        qimage (QtGui.QImage):
            Internal QImage created from the NumPy buffer.
    """

    def __init__(self, image, **kwargs):
        """Initialize the pixmap from a NumPy image.

        Args:
            image (numpy.ndarray):
                Input RGB or RGBA image.

            **kwargs:
                Reserved for future extensions.
        """

        # Initialize the base QPixmap.
        super(ImageDataPixmap, self).__init__()

        # Extract the image dimensions.
        height, width, channels = image.shape

        # Determine the Qt image format.
        if channels >= 4:

            # Use RGBA format.
            qt_format = QtGui.QImage.Format.Format_RGBA8888

            # Bytes per image row.
            bytes_per_line = width * 4
        else:
            # Use RGB format.
            qt_format = QtGui.QImage.Format.Format_RGB888

            # Bytes per image row.
            bytes_per_line = width * 3

        # Create a QImage that references the NumPy buffer.
        self.qimage = QtGui.QImage(image.data, width, height, bytes_per_line, qt_format)

        # Convert the QImage into a QPixmap.
        self.convertFromImage(self.qimage)


class NullPixmap(QtGui.QPixmap):
    """Empty pixmap.

    This class creates an empty ``QPixmap`` that can be used as a default placeholder where no valid image is available.
    """

    def __init__(self, *args, **kwargs):
        """Initialize an empty pixmap.

        Args:
            *args:
                Additional positional arguments.

            **kwargs:
                Reserved for future extensions.
        """

        # Initialize the base QPixmap.
        super(NullPixmap, self).__init__()


if __name__ == "__main__":
    pass
