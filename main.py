import sys

from PySide6 import QtWidgets

from widgets.login import ensure_login
from widgets import MainWindow


def main():
    """
    Application entry point.
    """

    app = QtWidgets.QApplication(sys.argv)

    # Require an AYON login (auto-login if 'Remember me' was used) before the UI.
    if not ensure_login():
        sys.exit(0)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
