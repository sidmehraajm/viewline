"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./widgets/categorydialog.py

Description:
    Dialog for selecting a Viewline source category.

This module provides a simple modal dialog that allows users to choose
between the supported source categories before performing an operation.

Responsibilities:
    - Display available source categories.
    - Allow the user to select a single category.
    - Return the selected category to the caller.
    - Handle dialog acceptance and cancellation.

Features:
    - Radio button category selection.
    - Button group for exclusive selection.
    - Apply and Close actions.
    - Returns the selected category identifier.

Architecture:
    CategoryDialog
        ├── VerticalLayout
        │     ├── USD Radio Button
        │     ├── Media Radio Button
        │     └── HorizontalLayout
        │            ├── Spacer
        │            ├── Close Button
        │            └── Apply Button
        │
        └── Returns selected category

Nodes:
    CategoryDialog
"""

from __future__ import absolute_import

from PySide6 import QtWidgets

from viewline import logger

from viewline.widgets.buttons import TextButton

from viewline.widgets.layouts import VerticalLayout
from viewline.widgets.layouts import HorizontalLayout
from viewline.widgets.layouts import HorizontalSpacer

LOGGER = logger.getLogger(__name__)


class CategoryDialog(QtWidgets.QDialog):
    """Dialog used to select a Viewline source category.

    The dialog presents the supported source categories and allows the user to select one before continuing.

    Attributes:
        ids (dict[int, str]):
            Mapping between button IDs and category names.

        replay (str | None):
            Selected category after the dialog is accepted.
            Returns ``None`` when the dialog is cancelled.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the category selection dialog.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.
        """

        # Initialize the base dialog.
        super().__init__(parent)

        # Category lookup table.
        self.ids = {1: "usd", 2: "media"}

        # Selected category.
        self.replay = None

        # Build the user interface.
        self.setupUi()

    def setupUi(self):
        """Create and configure the dialog widgets."""

        # Configure the dialog window.
        # Set initial dialog size
        self.resize(210, 140)
        self.setWindowTitle("Choose a category")

        # Create the main layout.
        self.verticallayout = VerticalLayout(self, space=10, margins=(20, 20, 20, 20))

        # Create an exclusive radio button group.
        self.buttonGroup = QtWidgets.QButtonGroup(self)

        # ------------------------------------------------------------------
        # Media category.
        # ------------------------------------------------------------------

        # Create the media radio button.
        self.medaiRadiobutton = QtWidgets.QRadioButton(self)

        # Display the category label.
        self.medaiRadiobutton.setText(self.ids[2])

        # Register the button with its identifier.
        self.buttonGroup.addButton(self.medaiRadiobutton, id=2)

        # Add the button to the layout.
        self.verticallayout.addWidget(self.medaiRadiobutton)

        # ------------------------------------------------------------------
        # USD category.
        # ------------------------------------------------------------------

        # Create the USD radio button.
        self.usdRadiobutton = QtWidgets.QRadioButton(self)

        # Display the category label.
        self.usdRadiobutton.setText(self.ids[1])

        # Register the button with its identifier.
        self.buttonGroup.addButton(self.usdRadiobutton, id=1)

        # Add the button to the layout.
        self.verticallayout.addWidget(self.usdRadiobutton)

        # ------------------------------------------------------------------
        # Bottom buttons.
        # ------------------------------------------------------------------

        # Create the button layout.
        self.horizontalayout2 = HorizontalLayout(None, space=5, margins=(5, 5, 5, 5))

        # Add the button layout.
        self.verticallayout.addLayout(self.horizontalayout2)

        # Push buttons to right side
        self.horizontalspacer = HorizontalSpacer()
        self.horizontalayout2.addItem(self.horizontalspacer)

        # Close button
        self.closeButton = TextButton(self, label="Close")
        self.horizontalayout2.addWidget(self.closeButton)

        # Apply button
        self.applyButton = TextButton(self, label="Apply and Close")
        self.horizontalayout2.addWidget(self.applyButton)

        # Connect button signals.
        self.closeButton.clicked.connect(self.close)
        self.applyButton.clicked.connect(self.apply)

    def apply(self):
        """Accept the selected category and close the dialog."""

        # Retrieve the selected radio button.
        checked_button = self.buttonGroup.checkedButton()

        # Nothing selected.
        if not checked_button:
            return

        # Retrieve the selected button ID.
        checked_id = self.buttonGroup.checkedId()

        # Log the selected category.
        LOGGER.info(f"Checked Category: {self.ids[checked_id]}")

        # Store the selected category.
        self.replay = self.ids[checked_id]

        # Close the dialog with an accepted state.
        self.accept()

    def closeEvent(self, event):
        """Handle dialog close events.

        Args:
            event (QtGui.QCloseEvent):
                Qt close event.
        """

        # Clear the current selection.
        self.replay = None

        # Accept the close request.
        event.accept()


if __name__ == "__main__":
    pass
