"""
AYON login dialog for Viewline.

Mirrors the folder-publisher's auth flow: username/password sign-in against the
AYON server using ``ayon_api.GlobalServerAPI().login()``, with a "Remember Me"
option persisted via QSettings. On success the global ayon_api connection is
established, which scripts/ayon_provider.py then reuses.

Usage (from main.py):
    from viewline.widgets.login import ensure_login
    if not ensure_login():
        sys.exit(0)
"""

from __future__ import absolute_import

import os
import base64
import logging

from PySide6 import QtCore
from PySide6 import QtWidgets

try:
    import ayon_api
except ImportError:
    ayon_api = None

LOGGER = logging.getLogger("viewline.login")

ORG = "MotionCraft"
APP = "Viewline"


def _do_login(url, user, password):
    """Log in to AYON and return the authenticated user name."""
    os.environ["AYON_SERVER_URL"] = url
    ayon_api.close_connection()
    con = ayon_api.GlobalServerAPI()
    con.login(user, password)
    return con.get_user()["name"]


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setWindowTitle("Viewline — Sign in to AYON")
        self.setModal(True)
        self.setMinimumWidth(380)

        self.user_name = None
        self.settings = QtCore.QSettings(ORG, APP)

        form = QtWidgets.QFormLayout()
        self.input_url = QtWidgets.QLineEdit()
        self.input_url.setPlaceholderText("http://ayon:5000")
        self.input_user = QtWidgets.QLineEdit()
        self.input_user.setPlaceholderText("username")
        self.input_pass = QtWidgets.QLineEdit()
        self.input_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.cb_remember = QtWidgets.QCheckBox("Remember me")

        form.addRow("Server:", self.input_url)
        form.addRow("User:", self.input_user)
        form.addRow("Password:", self.input_pass)
        form.addRow("", self.cb_remember)

        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet("color: #d05050;")
        self.status.setWordWrap(True)

        self.btn_login = QtWidgets.QPushButton("Sign In")
        self.btn_login.setDefault(True)
        self.btn_login.clicked.connect(self.accept_login)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.status)
        layout.addWidget(self.btn_login)

        # Prefill from remembered settings.
        self.input_url.setText(self.settings.value("ayon_url", "") or "")
        self.input_user.setText(self.settings.value("ayon_user", "") or "")
        b64 = self.settings.value("ayon_pass", "") or ""
        if b64:
            try:
                self.input_pass.setText(base64.b64decode(b64.encode()).decode())
                self.cb_remember.setChecked(True)
            except Exception:
                pass

        self.input_pass.returnPressed.connect(self.accept_login)

    def accept_login(self):
        url = self.input_url.text().strip()
        user = self.input_user.text().strip()
        pw = self.input_pass.text()

        if not (url and user and pw):
            self.status.setText("Please fill server, user and password.")
            return

        self.btn_login.setEnabled(False)
        self.status.setStyleSheet("color: #888;")
        self.status.setText("Signing in…")
        QtWidgets.QApplication.processEvents()

        try:
            name = _do_login(url, user, pw)
        except Exception as exc:
            self.status.setStyleSheet("color: #d05050;")
            self.status.setText("Login failed: %s" % exc)
            self.btn_login.setEnabled(True)
            return

        # Persist remember-me choice.
        self.settings.setValue("ayon_url", url)
        self.settings.setValue("ayon_user", user)
        if self.cb_remember.isChecked():
            self.settings.setValue(
                "ayon_pass", base64.b64encode(pw.encode()).decode()
            )
        else:
            self.settings.remove("ayon_pass")

        self.user_name = name
        self.accept()


def ensure_login():
    """Ensure an AYON session exists.

    Tries a silent auto-login with remembered credentials first; otherwise shows
    the login dialog. Returns True if authenticated, False if the user cancelled.
    If ayon_api is unavailable, returns True so the provider can fall back to an
    API key from the environment.
    """
    if ayon_api is None:
        LOGGER.warning("ayon_api not available; skipping login dialog.")
        return True

    settings = QtCore.QSettings(ORG, APP)
    url = settings.value("ayon_url", "") or ""
    user = settings.value("ayon_user", "") or ""
    b64 = settings.value("ayon_pass", "") or ""

    if url and user and b64:
        try:
            pw = base64.b64decode(b64.encode()).decode()
            _do_login(url, user, pw)
            LOGGER.info("Auto-login successful for %s", user)
            return True
        except Exception:
            settings.remove("ayon_pass")

    dialog = LoginDialog()
    return dialog.exec() == QtWidgets.QDialog.Accepted
