"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./widgets/checkboxs.py

Description:
    Custom checkbox widget used throughout Viewline.

    This module provides a lightweight wrapper around Qt's QCheckBox, adding
    convenient initialization options for text, checked state, and layout direction.

Responsibilities:
    - Create a reusable checkbox widget.
    - Initialize common checkbox properties.
    - Support configurable checked state.
    - Support configurable layout direction.

Features:
    - Custom label initialization.
    - Optional default checked state.
    - Configurable text direction.
    - Lightweight wrapper around QCheckBox.

Architecture:
    NormalCheckbox
        └── QtWidgets.QCheckBox

Nodes:
    NormalCheckbox
"""

from __future__ import absolute_import

from PySide6 import QtCore
from PySide6 import QtWidgets


class NormalCheckbox(QtWidgets.QCheckBox):
    """Custom checkbox widget.

    A reusable checkbox widget that simplifies initialization by allowing the label, checked state,
    and layout direction to be configured during construction.

    Attributes:
        text (str):
            Checkbox label.

        checked (bool):
            Initial checked state.

        direction (QtCore.Qt.LayoutDirection):
            Layout direction used for the checkbox.
    """

    def __init__(self, parent, label, **kwargs):
        """Initialize the checkbox widget.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            label (str):
                Checkbox text.

            **kwargs:
                Optional keyword arguments.

                checked (bool):
                    Initial checked state.
                    Defaults to False.

                direction (QtCore.Qt.LayoutDirection):
                    Checkbox layout direction.
                    Defaults to LeftToRight.
        """

        # Initialize the base QCheckBox.
        super(NormalCheckbox, self).__init__(parent)

        # Set the checkbox label.
        self.setText(label)

        # Apply the initial checked state.
        self.setChecked(kwargs.get("checked", False))

        # Read the requested layout direction.
        direction = kwargs.get("direction", QtCore.Qt.LayoutDirection.LeftToRight)

        # Apply the layout direction.
        self.setLayoutDirection(direction)


if __name__ == "__main__":
    pass
