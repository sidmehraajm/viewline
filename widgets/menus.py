"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./widgets/menus.py

Description:
    This module contains reusable Qt menu and action wrappers used throughout the Review Player application.

The module primarily provides:
    - Watermark display menus
    - Overlay visibility controls
    - QAction wrapper utilities
    - Dynamic watermark configuration support

Main Components:
    WatermarkMenus:
        Dynamic watermark overlay menu system.

    WatermarkAction:
        Reusable QAction wrapper for overlay controls.

Features:
    - Watermark preset loading
    - Dynamic overlay toggles
    - Version/media watermark updates
    - Overlay state management
    - Signal-based UI communication
"""

from __future__ import absolute_import


from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

from viewline import utils
from viewline import resources

from widgets.pixmaps import NamePixmapIcon


class NormalAction(QtGui.QAction):
    """Standard menu action.

    This class extends ``QAction`` by providing a simplified constructor for creating menu actions with optional icons,
    tooltips, enabled state, and checkable behavior.

    Attributes:
        None.
    """

    def __init__(self, parent, label, **kwargs):
        """Initialize a menu action.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            label (str):
                Action text.

            **kwargs:
                Optional keyword arguments.

                enable (bool):
                    Initial enabled state.

                tooltip (str):
                    Action tooltip.

                checkable (bool):
                    Enable checkable state.

                icon (str):
                    Icon resource name.
        """

        # Initialize the base QAction.
        super(NormalAction, self).__init__(parent)

        # Determine whether the action is enabled.
        enable = True if kwargs.get("enable") is None else kwargs["enable"]

        # Set the action text.
        self.setText(label)

        # Enable or disable the action.
        self.setEnabled(enable)

        # Set the tooltip.
        self.setToolTip(kwargs.get("tooltip", label))

        # Configure as a checkable action.
        if kwargs.get("checkable"):
            # Enable check state.
            self.setCheckable(True)

            # Default to unchecked.
            self.setChecked(False)

        # Assign an icon if available.
        if kwargs.get("icon"):
            # Load the icon resource.
            icon = NamePixmapIcon(kwargs.get("icon"))

            # Apply the icon.
            self.setIcon(icon)


class WatermarkAction(QtGui.QAction):
    """
    Watermark display QAction wrapper.

    This action represents an individual watermark toggle item inside the display menu.

    Features:
        - Checkable overlay state
        - Enable/disable support
        - Dynamic watermark labels

    Example:
        >>> action = WatermarkAction(menu, "project", True)
    """

    def __init__(self, parent, text, checked, **kwargs):
        """
        Initialize display action.

        Args:
            parent (QtWidgets.QWidget):
                Parent menu.

            text (str):
                Action display label.

            checked (bool):
                Initial checked state.

            **kwargs:
                Optional keyword arguments.

                enable (bool):
                    Enable or disable the action.
        """

        super(WatermarkAction, self).__init__(parent)

        # Resolve enabled state
        enable = True if kwargs.get("enable") is None else kwargs["enable"]

        # Configure action
        self.setCheckable(True)
        self.setChecked(checked)
        self.setText(text)
        self.setEnabled(enable)


class WatermarkMenus(QtWidgets.QMenu):
    """
    This menu dynamically builds watermark toggle actions from the ``watermarks.json`` preset configuration file.

    The menu is primarily used by the viewer overlay system to:

    - Enable or disable watermark items
    - Update watermark values from media/version data
    - Clear active watermark values
    - Emit UI display state changes

    Signals:
        display_changed (bool, str, str, dict):
            Emitted whenever a watermark action is toggled.

            Arguments:
                checked (bool):
                    Current checked state.

                key (str):
                    Watermark code/key.

                position (str):
                    Watermark screen position.

                param (dict):
                    Full watermark configuration dictionary.

    Example:
        >>> menu = WatermarkMenus(parent)
        >>> menu.display_changed.connect(callback)
    """

    display_changed = QtCore.Signal(bool, str, str, dict)

    def __init__(self, parent, **kwargs):
        """
        Initialize display watermark menu.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.
        """

        super().__init__(parent)

        # Configure menu
        self.setTitle("Display")
        self.setTearOffEnabled(True)

        # Load watermark preset configuration
        self.watermarks = resources.getPreset("watermarks")

        # Build watermark actions
        for position, values in self.watermarks.items():
            for context in values:
                # Skip disabled overlays
                if not context.get("enable"):
                    continue

                # Create menu action
                action = WatermarkAction(
                    self, context["code"], context["checked"], enable=context["enable"]
                )
                self.addAction(action)

                # Emit overlay state changes
                action.toggled.connect(
                    lambda checked, key=context[
                        "code"
                    ], pos=position, param=context: self.display_changed.emit(
                        checked, key, pos, param
                    )
                )

    def update_watermarks(self, inputs, **kwargs):
        """
        Override watermark values from version/media context.
        This updates overlay text and image values dynamically based on the currently loaded media/version data.

        Args:
            inputs (dict):
                Version/media data dictionary.

            **kwargs:
                Additional override values such as:

                - studio_logo
                - project_logo

        Example:
            >>> menu.update_watermarks(version)
        """

        self.watermarks = utils.overrideWatermarkValues(
            inputs, watermarks=self.watermarks, **kwargs
        )

    def clear_watermarks(self):
        """
        Clear all watermark display values.
        This preserves watermark configuration and visibility states but removes current overlay values.
        """

        for position in self.watermarks:
            for overlay in self.watermarks[position]:
                # Skip disabled overlays
                if not overlay.get("enable"):
                    continue

                # Reset overlay value
                overlay["value"] = None


class Viewer2dMenubar(QtWidgets.QToolBar):
    """Toolbar for the 2D viewer.

    This toolbar acts as a placeholder for future 2D viewer controls. It provides a common toolbar interface so both the 2D and 3D viewers share a consistent layout.

    Attributes:
        None.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the 2D viewer toolbar.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            **kwargs:
                Reserved for future extensions.
        """

        # Initialize the base toolbar.
        super().__init__(parent)


class Viewer3dMenubar(QtWidgets.QToolBar):
    """Toolbar for the USD 3D viewer.

    This toolbar provides controls for viewport rendering, including shading modes, render complexity, display purposes, scene materials, grid visibility, and camera selection.

    Signals:
        shading_changed (str):
            Emitted when the shading mode changes.

        complexity_changed (float):
            Emitted when render complexity changes.

        purposes_changed (str):
            Emitted when a display purpose is toggled.

        materials_enable (bool):
            Emitted when scene materials are enabled or disabled.

        grid_enable (bool):
            Emitted when the viewport grid is toggled.

        camera_changed (str):
            Emitted when the active camera changes.
    """

    # Emitted when the shading mode changes.
    shading_changed = QtCore.Signal(str)

    # Emitted when render complexity changes.
    complexity_changed = QtCore.Signal(float)

    # Emitted when display purposes change.
    purposes_changed = QtCore.Signal(str)

    # Emitted when scene materials are enabled or disabled.
    materials_enable = QtCore.Signal(bool)

    # Emitted when grid visibility changes.
    grid_enable = QtCore.Signal(bool)

    # Emitted when the active camera changes.
    camera_changed = QtCore.Signal(str)

    def __init__(self, parent, **kwargs):
        """Initialize the 3D viewer toolbar.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            **kwargs:
                Reserved for future extensions.
        """

        # Initialize the base toolbar.
        super().__init__(parent)

        # Create the Display toolbar button.
        self.displayButton = QtWidgets.QToolButton()

        # Set the button label.
        self.displayButton.setText("Display")

        # Show the menu from the button.
        self.displayButton.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)

        # Add the button to the toolbar.
        self.addWidget(self.displayButton)

        # Create the Display menu.
        self.displayMenu = QtWidgets.QMenu(self)

        # Assign the menu to the button.
        self.displayButton.setMenu(self.displayMenu)

        # Available viewport shading modes.
        draw_modes = [
            ("Wireframe", "DRAW_WIREFRAME", False),
            ("Wireframe on Surface", "DRAW_WIREFRAME_ON_SURFACE", False),
            ("Shader Smooth", "DRAW_SHADED_SMOOTH", True),
            ("Shader Flat", "DRAW_SHADED_FLAT", False),
            ("Points", "DRAW_POINTS", False),
            ("Geom Only", "DRAW_GEOM_ONLY", False),
            ("Geom Smooth", "DRAW_GEOM_SMOOTH", False),
            ("Geom Flat", "DRAW_GEOM_FLAT", False),
        ]

        # Create the shading submenu.
        self.shadingModeMenu, self.shadingModeGroup = self.addActionGroup(
            self.displayMenu, "Shading Mode", draw_modes, tearOff=True, exclusive=True
        )

        # Separate menu sections.
        self.displayMenu.addSeparator()

        # Available render complexity levels.
        complexities = [
            ("Low", 1.0, True),
            ("Medium", 1.1, False),
            ("High", 1.2, False),
            ("Very High", 1.3, False),
        ]

        # Create the complexity submenu.
        self.complexityMenu, self.complexityGroup = self.addActionGroup(
            self.displayMenu, "Complexity", complexities, tearOff=True, exclusive=True
        )

        # Separate menu sections.
        self.displayMenu.addSeparator()

        # Display purpose options.
        purposes = [
            ("Guide", "showGuides", True),
            ("Proxy", "showProxy", False),
            ("Render", "showRender", False),
        ]

        # Create the display purpose submenu.
        self.purposesMenu, self.purposesGroup = self.addActionGroup(
            self.displayMenu, "Display Purposes", purposes, tearOff=True, exclusive=False
        )

        # Separate menu sections.
        self.displayMenu.addSeparator()

        # Toggle scene materials.
        self.enableMaterialsAction = NormalAction(self, "Enable Scene Materials", checkable=True)
        self.displayMenu.addAction(self.enableMaterialsAction)

        # Separate menu sections.
        self.displayMenu.addSeparator()

        # Toggle viewport grid.
        self.gridAction = NormalAction(self, "Grid", checkable=True)
        self.gridAction.setVisible(False)
        self.displayMenu.addAction(self.gridAction)

        # Create the Camera toolbar button.
        self.cameraButton = QtWidgets.QToolButton()
        self.cameraButton.setText("Camera")
        self.cameraButton.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)

        # Add the camera button.
        self.addWidget(self.cameraButton)

        # Create the camera menu.
        self.cameraMenu = QtWidgets.QMenu(self)
        self.cameraButton.setMenu(self.cameraMenu)

        # Camera action group.
        self.cameraGroup = QtGui.QActionGroup(self.cameraMenu)
        self.cameraGroup.setExclusive(True)

        # Connect shading selection.
        self.shadingModeGroup.triggered.connect(self.shadingModeChanged)

        # Connect complexity selection.
        self.complexityGroup.triggered.connect(self.complexityModeChanged)

        # Connect purpose selection.
        self.purposesGroup.triggered.connect(self.purposesModeChanged)

        # Connect material toggle.
        self.enableMaterialsAction.triggered.connect(self.enableMaterials)

        # Connect grid toggle.
        self.gridAction.triggered.connect(self.enableGrid)

        # Connect camera selection.
        self.cameraGroup.triggered.connect(self.selectCamera)

    def addActionGroup(self, parentMenu, title, items, tearOff=False, exclusive=False):
        """Create a submenu containing grouped actions.

        Args:
            parentMenu (QtWidgets.QMenu):
                Parent menu.

            title (str):
                Menu title.

            items (list):
                List of action definitions.

            tearOff (bool):
                Enable tear-off menu.

            exclusive (bool):
                Allow only one checked action.

        Returns:
            tuple:
                Created menu and QActionGroup.
        """

        # Create the submenu.
        menu = QtWidgets.QMenu(title, self)

        # Enable tear-off if requested.
        menu.setTearOffEnabled(tearOff)

        # Add the submenu.
        parentMenu.addMenu(menu)

        # Create the action group.
        group = QtGui.QActionGroup(menu)

        # Configure exclusivity.
        group.setExclusive(exclusive)

        # Create actions.
        for text, data, checked in items:

            # Create the action.
            action = NormalAction(self, text, checkable=True)

            # Set the default state.
            action.setChecked(checked)

            # Store user data.
            if data:
                action.setData(data)

            # Register with the group.
            group.addAction(action)

            # Add to the menu.
            menu.addAction(action)

        return menu, group

    def shadingModeChanged(self, action):
        """Handle shading mode changes.

        Args:
            action (QtGui.QAction):
                Selected shading action.
        """
        # Notify listeners.
        self.shading_changed.emit(action.data())

    def complexityModeChanged(self, action):
        """Handle complexity changes.

        Args:
            action (QtGui.QAction):
                Selected complexity action.
        """

        # Notify listeners.
        self.complexity_changed.emit(action.data())

    def purposesModeChanged(self, action):
        """Handle display purpose changes.

        Args:
            action (QtGui.QAction):
                Selected display purpose.
        """

        # Notify listeners.
        self.purposes_changed.emit(action.data())

    def enableMaterials(self, action):
        """Handle material visibility changes.

        Args:
            action (bool):
                Checked state.
        """

        # Notify listeners.
        self.materials_enable.emit(action)

    def enableGrid(self, action):
        """Handle grid visibility changes.

        Args:
            action (bool):
                Checked state.
        """

        # Notify listeners.
        self.grid_enable.emit(action)

    def set_cameras(self, cameras):
        """Populate the camera menu.

        Args:
            cameras (list):
                List of available scene cameras.
        """

        # Remove existing camera actions.
        for action in self.cameraGroup.actions():
            action.deleteLater()

        # Add the default camera.
        cameras = [("Default", "/default", True)] + cameras

        # Create camera actions.
        for name, path, state in cameras:

            # Create the action.
            action = NormalAction(self, name, checkable=True)

            # Set the initial state.
            action.setChecked(state)

            # Store the camera path.
            action.setData(path)

            # Add to the menu.
            self.cameraMenu.addAction(action)

            # Register with the action group.
            self.cameraGroup.addAction(action)

    def selectCamera(self, action):
        """Handle camera selection.

        Args:
            action (QtGui.QAction):
                Selected camera action.
        """

        # Notify listeners.
        self.camera_changed.emit(action.data())


class ViewspanMenus(QtWidgets.QMenu):
    """Main File menu.

    This menu provides the primary file operations used by Viewline, including opening, saving, clearing, and exiting the application.
    Each menu action emits a signal that can be connected to the main application logic.

    Signals:
        open_action:
            Emitted when the Open action is triggered.

        clear_action:
            Emitted when the Clear action is triggered.

        save_action:
            Emitted when the Save action is triggered.

        exit_action:
            Emitted when the Exit action is triggered.
    """

    # Emitted when the Open action is selected.
    open_action = QtCore.Signal()

    # Emitted when the Clear action is selected.
    clear_action = QtCore.Signal()

    # Emitted when the Save action is selected.
    save_action = QtCore.Signal()

    # Emitted when the Exit action is selected.
    exit_action = QtCore.Signal()

    def __init__(self, parent, **kwargs):
        """Initialize the File menu.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            **kwargs:
                Reserved for future extensions.
        """

        # Initialize the base QMenu.
        super().__init__(parent)

        # Set the menu title.
        self.setTitle("File")

        # Allow the menu to be detached.
        self.setTearOffEnabled(True)

        # Create the Open action.
        self.openAction = NormalAction(self, "Open", icon="open", tooltip="Open Image")

        # Add the Open action.
        self.addAction(self.openAction)

        # Add a separator.
        self.addSeparator()

        # Create the Save action.
        self.saveAction = NormalAction(self, "Save", icon="save", tooltip="Save Image")

        # Add the Save action.
        self.addAction(self.saveAction)

        # Add a separator.
        self.addSeparator()

        # Create the Clear action.
        self.clearAction = NormalAction(self, "Clear", icon="clear", tooltip="Clear the View Panel")

        # Add the Clear action.
        self.addAction(self.clearAction)

        # Add a separator.
        self.addSeparator()

        # Create the Exit action.
        self.exitAction = NormalAction(self, "exit", icon="exit", tooltip="Exit from the tool")

        # Add the Exit action.
        self.addAction(self.exitAction)

        # Forward the Open signal.
        self.openAction.triggered.connect(lambda: self.open_action.emit())

        # Forward the Clear signal.
        self.clearAction.triggered.connect(lambda: self.clear_action.emit())

        # Forward the Save signal.
        self.saveAction.triggered.connect(lambda: self.save_action.emit())

        # Forward the Exit signal.
        self.exitAction.triggered.connect(lambda: self.exit_action.emit())


if __name__ == "__main__":
    pass
