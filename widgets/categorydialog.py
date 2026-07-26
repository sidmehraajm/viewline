from __future__ import absolute_import

from PySide6 import QtCore
from PySide6 import QtWidgets

from viewline import logger

from viewline.widgets.buttons import TextButton

from viewline.widgets.layouts import VerticalLayout
from viewline.widgets.layouts import HorizontalLayout
from viewline.widgets.layouts import HorizontalSpacer

LOGGER = logger.getLogger(__name__)


class CategoryDialog(QtWidgets.QDialog):

    def __init__(self, parent, **kwargs):

        # Initialize QDialog
        super().__init__(parent)

        self.ids = {1: "usd", 2: "media"}

        self.replay = None

        self.setupUi()

    def setupUi(self):
        """
        Build dialog user interface.
        """
        # Set initial dialog size
        self.resize(210, 140)

        # Set dialog title
        self.setWindowTitle("Choose a category")

        self.verticallayout = VerticalLayout(self, space=10, margins=(20, 20, 20, 20))

        self.buttonGroup = QtWidgets.QButtonGroup(self)

        self.medaiRadiobutton = QtWidgets.QRadioButton(self)
        self.medaiRadiobutton.setText(self.ids[2])
        # self.medaiRadiobutton.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        # radio_button.toggled.connect(lambda enabled: self.set_category(category, enabled))
        self.buttonGroup.addButton(self.medaiRadiobutton, id=2)
        self.verticallayout.addWidget(self.medaiRadiobutton)

        self.usdRadiobutton = QtWidgets.QRadioButton(self)
        self.usdRadiobutton.setText(self.ids[1])
        # self.usdRadiobutton.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        self.buttonGroup.addButton(self.usdRadiobutton, id=1)
        self.verticallayout.addWidget(self.usdRadiobutton)

        self.horizontalayout2 = HorizontalLayout(None, space=5, margins=(5, 5, 5, 5))
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

        self.closeButton.clicked.connect(self.close)
        self.applyButton.clicked.connect(self.apply)

    def apply(self):
        """
        Apply current settings and close dialog.

        Emits value_changed signal containing the
        current text formatting configuration.
        """

        # Option A: Get the QRadioButton object directly
        checked_button = self.buttonGroup.checkedButton()
        if not checked_button:
            return

        # Option B: Get the ID you assigned to the checked button
        checked_id = self.buttonGroup.checkedId()

        LOGGER.info(f"Checked Category: {self.ids[checked_id]}")

        self.replay = self.ids[checked_id]

        # Close dialog with Accepted state
        self.accept()

    def closeEvent(self, event):
        self.replay = None
        event.accept()


if __name__ == "__main__":
    pass
