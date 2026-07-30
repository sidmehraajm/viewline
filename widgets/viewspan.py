"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./constants/viewspan.py

Description:
    Main window for the Viewspan image preview application.

    This module provides the top-level window used for viewing still images and image sequences.
    It combines the menu system, image preview widget, application styling, and status information into a single user interface.

Responsibilities:
    - Create the main application window.
    - Manage menus and user actions.
    - Display image previews.
    - Handle open, save, and clear operations.
    - Apply application styling and icons.
    - Update the window title with image information.

Features:
    - File open dialog.
    - Image preview viewer.
    - Save preview image.
    - Clear preview image.
    - Dynamic window title updates.
    - Application icon support.
    - Theme stylesheet support.
    - Optional maximized startup.

Architecture:
    ViewspanWindow
        ├── QMenuBar
        │     └── ViewspanMenus
        ├── ViewspanWidget
        ├── CopyrightLabel
        └── SetStylesheet

Nodes:
    ViewspanWindow
"""

from __future__ import absolute_import

from PySide6 import QtWidgets

from viewline import utils
from viewline import logger
from viewline import constants

from viewline.widgets.dialogs import FileDialog
from viewline.widgets.menus import ViewspanMenus
from viewline.widgets.styles import SetStylesheet
from viewline.widgets.viewer import ViewspanWidget
from viewline.widgets.labels import CopyrightLabel
from viewline.widgets.layouts import VerticalLayout
from viewline.widgets.pixmaps import NamePixmapIcon

LOGGER = logger.getLogger(__name__)


class ViewspanWindow(QtWidgets.QMainWindow):
    """Main window for the Viewspan application.

    This window hosts the image preview widget, menu bar, and footer information.
    It provides the primary interface for loading, viewing, saving, and clearing preview images.

    Attributes:
        maximize (bool):
            Start the window maximized.

        current_theme (str):
            Active application theme name.

        browsepath (str | None):
            Last used file browser directory.

        viewspanWidget (ViewspanWidget):
            Central image preview widget.

        viewspanMenus (ViewspanMenus):
            Main File menu.

        copyrightLabel (CopyrightLabel):
            Footer copyright label.
    """

    def __init__(self, parent=None, **kwargs):
        """Initialize the main window.

        Args:
            parent (QtWidgets.QWidget, optional):
                Parent widget.

            **kwargs:
                Optional keyword arguments.

                maximize (bool):
                    Start maximized.
        """

        # Initialize the base QMainWindow.
        super(ViewspanWindow, self).__init__(parent)

        # Store startup options.
        self.maximize = kwargs.get("maximize", False)

        # Store the active theme.
        self.current_theme = constants.DEFAULT_THEME

        # Last used browse directory.
        self.browsepath = None

        # Build the user interface.
        self.setupUi()

        # Configure icons.
        self.setupIcons()

    def setupUi(self):
        """Build the main window interface."""

        # Set the default window size.
        self.resize(1400, 800)

        # Set the initial window title.
        self.setWindowTitle(f"{constants.VS_TOOL_NAME}-{constants.VL_VERSION}")

        # Create the central widget.
        self.centralwidget = QtWidgets.QWidget(self)

        # Assign the central widget.
        self.setCentralWidget(self.centralwidget)

        # Create the main layout.
        self.verticallayout = VerticalLayout(self.centralwidget, space=10, margins=(10, 10, 10, 10))

        # Create the menu bar.
        self.menubar = QtWidgets.QMenuBar(self)

        # Assign the menu bar.
        self.setMenuBar(self.menubar)

        # Create the File menu.
        self.viewspanMenus = ViewspanMenus(self.menubar)

        # Add the File menu to the menu bar.
        self.menubar.addAction(self.viewspanMenus.menuAction())

        # Create the image preview widget.
        self.viewspanWidget = ViewspanWidget(self)

        # Add the preview widget.
        self.verticallayout.addWidget(self.viewspanWidget)

        # Create the footer label.
        self.copyrightLabel = CopyrightLabel(self)

        # Add the footer label.
        self.verticallayout.addWidget(self.copyrightLabel)

        # Connect menu actions.
        self.viewspanMenus.open_action.connect(self.openImage)
        self.viewspanMenus.clear_action.connect(self.clearPanel)
        self.viewspanMenus.save_action.connect(self.saveImage)
        self.viewspanMenus.exit_action.connect(self.close)

        # Start maximized if requested.
        if self.maximize:
            self.showMaximized()

        # Apply the application stylesheet.
        SetStylesheet(self, theme=self.current_theme)

    def setupIcons(self):
        """Set the application window icon."""

        # Load the application icon.
        pixmap = NamePixmapIcon(constants.VS_TOOL_ICON)

        # Apply the window icon.
        self.setWindowIcon(pixmap)

    def openImage(self):
        """Open an image from disk."""

        # Create the file dialog.
        fileDialog = FileDialog(
            self,
            "Browse your image file",
            label="image",
            extensions=constants.IMAGE_EXTENSIONS,
            browsepath=self.browsepath,
        )

        # Show the file picker.
        filepath = fileDialog.pickFile()

        # Ignore cancellation.
        if not filepath:
            return

        # Remember the browse directory.
        self.browsepath = utils.dirname(filepath)

        # Load the image preview.
        self.viewspanWidget.set_image_preview(filepath)

        # Query the image resolution.
        resolution = self.viewspanWidget.resolution()

        # Update the window title.
        self.setWindowTitle(
            f"{constants.VS_TOOL_NAME}-{constants.VL_VERSION} ./{utils.fileName(filepath, extension=True)} ( {resolution} )"
        )

    def set_pixmap_preview(self, pixmap, label):
        """Display a pixmap preview.

        Args:
            pixmap (QtGui.QPixmap):
                Preview pixmap.

            label (str):
                Title label.
        """

        # Display the pixmap preview.
        self.viewspanWidget.set_pixmap_preview(pixmap)

        # Query the image resolution.
        resolution = self.viewspanWidget.resolution()

        # Update the window title.
        self.setWindowTitle(
            f"{constants.VS_TOOL_NAME}-{constants.VL_VERSION} {label} ( {resolution} )"
        )

    def clearPanel(self):
        """Clear the current preview image."""

        # Clear the preview widget.
        self.viewspanWidget.clear_preview()

    def saveImage(self):
        """Save the current preview image."""

        # Create the save file dialog.
        fileDialog = FileDialog(
            self,
            "Browse your Save directory",
            label="Image",
            extensions=["png", "jpg"],
            browsepath=None,
        )

        # Default output filename.
        filename = f"untitled.{constants.VL_START_FRAME:04d}"

        # Show the save dialog.
        filepath = fileDialog.savefile(filename)

        # Ignore cancellation.
        if not filepath:
            return

        # Remember the save directory.
        self.browsepath = utils.dirname(filepath)

        # Save the preview image.
        self.viewspanWidget.save_image_preview(filepath)


if __name__ == "__main__":
    pass
