"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./widgets/fontdialog.py

Description:
    Color filter editor for the Viewline viewer.

    This module provides the user interface for adjusting image display, color grading, visual styles, and image filtering.
    The widgets expose parameter controls that immediately update the active viewer through Qt signals.

Responsibilities:
    - Provide display adjustment controls.
    - Provide style adjustment controls.
    - Provide image filter controls.
    - Manage parameter reset operations.
    - Emit parameter update signals.

Features:
    - Tabbed interface.
    - Display parameter controls.
    - Style parameter controls.
    - Filter parameter controls.
    - Color picker support.
    - Slider-based editing.
    - Reset individual parameters.
    - Live viewer updates.

Architecture:
    ColorFilterWidget
        ├── DisplayWidget
        ├── StylesWidget
        └── FilterWidget

Nodes:
    ColorFilterWidget
    DisplayWidget
    StylesWidget
    FilterWidget
"""

from __future__ import absolute_import

from PySide6 import QtCore
from PySide6 import QtWidgets

from viewline import constants

from parameters import StyleSettings
from parameters import FilterSettings
from parameters import DisplaySettings


from viewline.widgets.buttons import TextButton
from viewline.widgets.buttons import ColorButton
from viewline.widgets.buttons import ResetButton

from viewline.widgets.labels import RightLabel

from viewline.widgets.sliders import NormalSlider

from viewline.widgets.pixmaps import NamePixmapIcon

from viewline.widgets.layouts import GridLayout
from viewline.widgets.layouts import VerticalSpacer
from viewline.widgets.layouts import VerticalLayout
from viewline.widgets.layouts import HorizontalLayout
from viewline.widgets.layouts import HorizontalSpacer


class ColorFilterWidget(QtWidgets.QWidget):
    """Main color filter editor.

    This widget acts as the container for all image adjustment controls.
    It organizes the Display, Styles, and Filter editors into a tabbed interface and provides a button for closing the window.

    Attributes:
        tabWidget (QtWidgets.QTabWidget):
            Container for all parameter pages.

        displayWidget (DisplayWidget):
            Display adjustment controls.

        stylesWidget (StylesWidget):
            Style adjustment controls.

        filterWidget (FilterWidget):
            Image filter controls.

        closeButton (TextButton):
            Button used to close the editor.
    """

    def __init__(self, parent, *args, **kwargs):
        """Initialize the color filter editor.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            *args:
                Additional positional arguments.

            **kwargs:
                Additional keyword arguments.
        """

        # Initialize the base QWidget.
        super(ColorFilterWidget, self).__init__(parent)

        # Build the user interface.
        self.setupUi()

        # Configure icons and window appearance.
        self.setupIcons()

    def setupUi(self):
        """Build the user interface.

        Creates the tab widget, parameter pages, layouts, and action buttons.
        """

        # Set the default window size.
        self.resize(410, 400)

        # Set the window title.
        self.setWindowTitle("Color Filter")

        # Create the main vertical layout.
        self.verticallayout = VerticalLayout(self, space=10, margins=(10, 10, 10, 10))

        # Create the tab widget.
        self.tabWidget = QtWidgets.QTabWidget(self)

        # Add the tab widget.
        self.verticallayout.addWidget(self.tabWidget)

        # Create the Display page.
        self.displayWidget = DisplayWidget(self.tabWidget)

        # Add the Display tab.
        self.tabWidget.addTab(self.displayWidget, "Display")

        # Create the Styles page.
        self.stylesWidget = StylesWidget(self)

        # Add the Styles tab.
        self.tabWidget.addTab(self.stylesWidget, "Styles")

        # Create the Filter page.
        self.filterWidget = FilterWidget(self)

        # Add the Filter tab.
        self.tabWidget.addTab(self.filterWidget, "Filter")

        # Create the bottom button layout.
        self.horizontallayout = HorizontalLayout(None, space=10, margins=(5, 5, 5, 5))

        # Add the button layout.
        self.verticallayout.addLayout(self.horizontallayout)

        # Push buttons to the right.
        self.horizontalspacer1 = HorizontalSpacer()

        # Add the spacer.
        self.horizontallayout.addItem(self.horizontalspacer1)

        # Create the Close button.
        self.closeButton = TextButton(None, label="Close", tooltip="Close the Color Filter")

        # Add the Close button.
        self.horizontallayout.addWidget(self.closeButton)

        # Show the Display tab by default.
        self.tabWidget.setCurrentIndex(0)

        # Connect the Close button.
        self.closeButton.clicked.connect(self.close)

    def setupIcons(self):
        """
        Setup the main window icon.
        """

        # Create the window icon.
        pixmap = NamePixmapIcon(constants.VL_COLOR_FILTER_TOOL_ICON)

        # Apply the icon.
        self.setWindowIcon(pixmap)

    def reset(self):
        """Reset all style parameters.

        Restores every style parameter to its default value.
        """

        # Reset all style controls.
        self.stylesWidget.reset_all()


class DisplayWidget(QtWidgets.QWidget):
    """Display parameter editor.

    This widget provides controls for adjusting image display properties such as exposure, gamma, gain, saturation,
    and overlay color. Each parameter is represented by a slider, while color parameters use a color picker.

    Any parameter changes are emitted immediately so the active viewer can update in real time.

    Attributes:
        display_changed (QtCore.Signal):
            Emitted whenever a display parameter changes.

        displaySettings (DisplaySettings):
            Collection of display parameter definitions.

        gridlayout (GridLayout):
            Layout containing all parameter controls.
    """

    # Emitted whenever a display parameter changes.
    display_changed = QtCore.Signal(object)

    def __init__(self, parent, *args, **kwargs):
        """Initialize the display parameter editor.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            *args:
                Additional positional arguments.

            **kwargs:
                Additional keyword arguments.
        """

        # Initialize the base QWidget.
        super(DisplayWidget, self).__init__(parent)

        # Create the display parameter collection.
        self.displaySettings = DisplaySettings()

        # Build the interface.
        self.setupUi()

    def setupUi(self):
        """Build the display parameter interface.

        Creates one row for every display parameter, including its label, slider, and reset button.
        """

        # Create the main layout.
        self.verticallayout = VerticalLayout(self, space=10, margins=(10, 10, 10, 10))

        # Create the parameter grid.
        self.gridlayout = GridLayout(None, space=(10, 20), margins=(20, 20, 20, 20))

        # Add the grid layout.
        self.verticallayout.addLayout(self.gridlayout)

        # Push controls toward the top.
        self.verticalSpacer = VerticalSpacer()

        # Add the spacer.
        self.verticallayout.addItem(self.verticalSpacer)

        # Retrieve all display parameters.
        parameters = self.displaySettings.parameters()

        # Build one row for each parameter.
        for index, parameter in enumerate(parameters):

            # Overlay uses a color picker.
            if parameter.name == "overlay":

                # Create the color selection button.
                widget = ColorButton(None, label=parameter.label, locked=False)

                # Update the parameter when the color changes.
                widget.color_changed.connect(
                    lambda clicked, inputs=(widget, parameter): self.color_changed(*inputs)
                )
            else:
                # Create a text label.
                widget = RightLabel(self, parameter.label)

            # Add the parameter label.
            self.gridlayout.addWidget(widget, index, 0, 1, 1)

            # Retrieve the slider range.
            minimum, maximum = parameter.slider_range()

            # Retrieve the initial slider value.
            value = parameter.slider_value()

            # Create the parameter slider.
            slider = NormalSlider(self, minimum=minimum, maximum=maximum, value=value)

            # Update the parameter while dragging.
            slider.valueChanged.connect(
                lambda xvalue, param=parameter: self.value_changed(param, xvalue)
            )

            # Add the slider.
            self.gridlayout.addWidget(slider, index, 1, 1, 1)

            # Create the reset button.
            resetButton = ResetButton(self, width=18, height=18)

            # Restore the default parameter value.
            resetButton.clicked.connect(
                lambda clicked, x=(slider, widget), param=parameter: self.reset(x, param)
            )

            # Add the reset button.
            self.gridlayout.addWidget(resetButton, index, 2, 1, 1)

    def color_changed(self, widget, parameter):
        """Update the selected color parameter.

        Args:
            widget (ColorButton):
                Color picker widget.

            parameter:
                Display parameter being modified.
        """

        # Store the selected color.
        parameter.set_color(widget.normalized_color)

        # Notify connected viewers.
        self.display_changed.emit(parameter)

    def value_changed(self, parameter, value):
        """Update a display parameter.

        Args:
            parameter:
                Parameter being modified.

            value (int):
                Slider value.
        """

        # Convert the slider value.
        value = parameter.value_from_slider(value)

        # Store the parameter value.
        parameter.value = value

        # Notify connected viewers.
        self.display_changed.emit(parameter)

    def reset(self, widgets, parameter):
        """Restore a parameter to its default value.

        Args:
            widgets (tuple):
                Slider and label widgets.

            parameter:
                Parameter to reset.
        """

        # Restore the default parameter value.
        parameter.reset()

        # Read the default slider value.
        value = parameter.slider_value()

        # Update the slider.
        widgets[0].setValue(value)

        # Restore the default overlay color.
        if isinstance(widgets[1], ColorButton):
            widgets[1].setColor((255, 0, 0))


class StylesWidget(QtWidgets.QWidget):
    """Style parameter editor.

    This widget provides controls for adjusting visual style parameters used by the viewer.
    Each style parameter is represented by a slider with an associated reset button.
    Parameter changes are emitted immediately so the viewer can update its appearance in real time.

    Attributes:
        style_changed (QtCore.Signal):
            Emitted whenever a style parameter changes.

        styleSettings (StyleSettings):
            Collection of style parameter definitions.

        parameters (list):
            List of available style parameters.

        gridlayout (GridLayout):
            Layout containing all parameter controls.
    """

    # Emitted whenever a style parameter changes.
    style_changed = QtCore.Signal(object)

    def __init__(self, parent, *args, **kwargs):
        """Initialize the style parameter editor.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            *args:
                Additional positional arguments.

            **kwargs:
                Additional keyword arguments.
        """

        # Initialize the base widget.
        super(StylesWidget, self).__init__(parent)

        # Create the style parameter collection.
        self.styleSettings = StyleSettings()

        # Build the user interface.
        self.setupUi()

    def setupUi(self):
        """Build the style parameter interface.

        Creates a row for each style parameter containing a label, slider, and reset button.
        """

        # Create the main vertical layout.
        self.verticallayout = VerticalLayout(self, space=10, margins=(10, 10, 10, 10))

        # Create the parameter grid layout.
        self.gridlayout = GridLayout(None, space=(10, 20), margins=(20, 20, 20, 20))

        # Add the grid layout.
        self.verticallayout.addLayout(self.gridlayout)

        # Push widgets toward the top.
        self.verticalSpacer = VerticalSpacer()

        # Add the spacer.
        self.verticallayout.addItem(self.verticalSpacer)

        # Retrieve all style parameters.
        self.parameters = self.styleSettings.parameters()

        # Create one row for each parameter.
        for index, parameter in enumerate(self.parameters):

            # Create the parameter label.
            widget = RightLabel(self, parameter.label)

            # Add the label.
            self.gridlayout.addWidget(widget, index, 0, 1, 1)

            # Get the slider range.
            minimum, maximum = parameter.slider_range()

            # Get the default slider value.
            value = parameter.slider_value()

            # Create the parameter slider.
            slider = NormalSlider(self, minimum=minimum, maximum=maximum, value=value)

            # Update the parameter while dragging.
            slider.valueChanged.connect(
                lambda xvalue, param=parameter: self.value_changed(param, xvalue)
            )

            # Add the slider.
            self.gridlayout.addWidget(slider, index, 1, 1, 1)

            # Create the reset button.
            resetButton = ResetButton(self, width=18, height=18)

            # Restore the default parameter value.
            resetButton.clicked.connect(
                lambda clicked, x=slider, param=parameter: self.reset(x, param)
            )

            # Add the reset button.
            self.gridlayout.addWidget(resetButton, index, 2, 1, 1)

    def value_changed(self, parameter, value):
        """Update a style parameter.

        Converts the slider position into the parameter's actual value and notifies connected viewers.

        Args:
            parameter:
                Style parameter being modified.

            value (int):
                Current slider position.
        """

        # Convert the slider value.
        value = parameter.value_from_slider(value)

        # Store the converted value.
        parameter.value = value

        # Notify connected widgets.
        self.style_changed.emit(parameter)

    def reset(self, slider, parameter):
        """Restore a parameter to its default value.

        Args:
            slider (NormalSlider):
                Slider associated with the parameter.

            parameter:
                Style parameter to restore.
        """

        # Restore the default parameter value.
        parameter.reset()

        # Read the default slider position.
        value = parameter.slider_value()

        # Update the slider.
        slider.setValue(value)


class FilterWidget(QtWidgets.QWidget):
    """Image filter parameter editor.

    This widget provides controls for adjusting image filter parameters such as sharpen, blur, edge detection, or other
    post-processing effects. Each parameter is represented by a slider with an associated reset button.
    Parameter changes are emitted immediately so the active viewer can update in real time.

    Attributes:
        filter_changed (QtCore.Signal):
            Emitted whenever a filter parameter changes.

        filterSettings (FilterSettings):
            Collection of available filter parameters.

        gridlayout (GridLayout):
            Layout containing all filter controls.
    """

    # Emitted whenever a filter parameter changes.
    filter_changed = QtCore.Signal(object)

    def __init__(self, parent, *args, **kwargs):
        """Initialize the filter parameter editor.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            *args:
                Additional positional arguments.

            **kwargs:
                Additional keyword arguments.
        """

        # Initialize the base widget.
        super(FilterWidget, self).__init__(parent)

        # Create the filter parameter collection.
        self.filterSettings = FilterSettings()

        # Build the user interface.
        self.setupUi()

    def setupUi(self):
        """Build the filter parameter interface.

        Creates one row for every filter parameter containing a label, slider, and reset button.
        """

        # Create the main vertical layout.
        self.verticallayout = VerticalLayout(self, space=10, margins=(10, 10, 10, 10))

        # Create the parameter grid.
        self.gridlayout = GridLayout(None, space=(10, 20), margins=(20, 20, 20, 20))

        # Add the grid layout.
        self.verticallayout.addLayout(self.gridlayout)

        # Push controls toward the top.
        self.verticalSpacer = VerticalSpacer()

        # Add the spacer.
        self.verticallayout.addItem(self.verticalSpacer)

        # Retrieve all filter parameters.
        parameters = self.filterSettings.parameters()

        # Create a row for each filter parameter.
        for index, parameter in enumerate(parameters):

            # Create the parameter label.
            widget = RightLabel(self, parameter.label)

            # Add the label.
            self.gridlayout.addWidget(widget, index, 0, 1, 1)

            # Get the slider range.
            minimum, maximum = parameter.slider_range()

            # Get the default slider value.
            value = parameter.slider_value()

            # Create the parameter slider.
            slider = NormalSlider(self, minimum=minimum, maximum=maximum, value=value)

            # Update the parameter while dragging.
            slider.valueChanged.connect(
                lambda xvalue, param=parameter: self.value_changed(param, xvalue)
            )

            # Add the slider.
            self.gridlayout.addWidget(slider, index, 1, 1, 1)

            # Create the reset button.
            resetButton = ResetButton(self, width=18, height=18)

            # Restore the default parameter value.
            resetButton.clicked.connect(
                lambda clicked, x=(slider, widget), param=parameter: self.reset(x, param)
            )

            # Add the reset button.
            self.gridlayout.addWidget(resetButton, index, 2, 1, 1)

    def value_changed(self, parameter, value):
        """Update a filter parameter.

        Converts the slider position into the corresponding parameter value and emits a notification so the viewer can refresh the displayed image.

        Args:
            parameter:
                Filter parameter being modified.

            value (int):
                Current slider position.
        """

        # Convert the slider value.
        value = parameter.value_from_slider(value)

        # Store the converted value.
        parameter.value = value

        # Notify connected widgets.
        self.filter_changed.emit(parameter)

    def reset(self, widgets, parameter):
        """Restore a filter parameter to its default value.

        Args:
            widgets (tuple):
                Tuple containing the slider and label widgets.

            parameter:
                Filter parameter to restore.
        """

        # Restore the default parameter value.
        parameter.reset()

        # Get the default slider position.
        value = parameter.slider_value()

        # Update the slider.
        widgets[0].setValue(value)

        # Restore the default color if the parameter is associated with a ColorButton.
        if isinstance(widgets[1], ColorButton):
            widgets[1].setColor((255, 0, 0))


if __name__ == "__main__":
    pass
