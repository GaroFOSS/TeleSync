import asyncio
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from auth_service import (
    complete_login_with_code,
    complete_login_with_password,
    request_login_code,
)
from config import AppConfig


class LoginDialog(QDialog):
    def __init__(self, config: AppConfig):
        super().__init__()

        self.config = config
        self.phone_code_hash: Optional[str] = None

        self.setWindowTitle("TeleSync Telegram Login")
        self.setMinimumWidth(460)
        self.setModal(True)

        title = QLabel("Login to Telegram")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        info = QLabel(
            "Enter your Telegram phone number, request a login code, "
            "then enter the code you receive in Telegram."
        )
        info.setWordWrap(True)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+5511999999999")

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Telegram login code")
        self.code_input.setEnabled(False)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Telegram 2FA password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setEnabled(False)

        self.status_label = QLabel("Not logged in.")
        self.status_label.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Phone:", self.phone_input)
        form.addRow("Code:", self.code_input)
        form.addRow("2FA Password:", self.password_input)

        self.request_code_button = QPushButton("Request Code")
        self.login_button = QPushButton("Login")
        self.cancel_button = QPushButton("Cancel")

        self.login_button.setEnabled(False)

        self.request_code_button.clicked.connect(self.request_code)
        self.login_button.clicked.connect(self.login)
        self.cancel_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(self.request_code_button)
        buttons.addWidget(self.login_button)
        buttons.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(info)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addWidget(self.status_label)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def set_busy(self, busy: bool) -> None:
        self.request_code_button.setEnabled(not busy)
        self.login_button.setEnabled(
            not busy and self.code_input.isEnabled()
        )
        self.cancel_button.setEnabled(not busy)

    def get_phone(self) -> str:
        return self.phone_input.text().strip()

    def request_code(self) -> None:
        phone = self.get_phone()

        if not phone:
            QMessageBox.warning(
                self,
                "Phone required",
                "Enter your Telegram phone number first.",
            )
            return

        self.set_busy(True)
        self.status_label.setText("Requesting Telegram login code...")

        try:
            result = asyncio.run(
                request_login_code(
                    config=self.config,
                    phone=phone,
                )
            )

            self.phone_code_hash = result.phone_code_hash

            self.code_input.setEnabled(True)
            self.login_button.setEnabled(True)
            self.phone_input.setEnabled(False)

            self.status_label.setText(
                "Code sent. Check your Telegram app and enter the code here."
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Login error",
                str(exc),
            )
            self.status_label.setText("Could not request login code.")

        finally:
            self.set_busy(False)

    def login(self) -> None:
        phone = self.get_phone()
        code = self.code_input.text().strip()
        password = self.password_input.text()

        if self.password_input.isEnabled():
            self.login_with_password(password)
            return

        if not code:
            QMessageBox.warning(
                self,
                "Code required",
                "Enter the Telegram login code first.",
            )
            return

        if not self.phone_code_hash:
            QMessageBox.warning(
                self,
                "Code not requested",
                "Request a login code before trying to log in.",
            )
            return

        self.set_busy(True)
        self.status_label.setText("Checking login code...")

        try:
            result = asyncio.run(
                complete_login_with_code(
                    config=self.config,
                    phone=phone,
                    code=code,
                    phone_code_hash=self.phone_code_hash,
                )
            )

            if result == "authorized":
                self.status_label.setText("Logged in successfully.")
                self.accept()
                return

            if result == "2fa_required":
                self.password_input.setEnabled(True)
                self.password_input.setFocus()
                self.status_label.setText(
                    "This Telegram account has two-step verification enabled. "
                    "Enter your Telegram password."
                )
                return

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Login error",
                str(exc),
            )
            self.status_label.setText("Could not complete login.")

        finally:
            self.set_busy(False)

    def login_with_password(self, password: str) -> None:
        if not password:
            QMessageBox.warning(
                self,
                "Password required",
                "Enter your Telegram two-step verification password.",
            )
            return

        self.set_busy(True)
        self.status_label.setText("Checking Telegram password...")

        try:
            result = asyncio.run(
                complete_login_with_password(
                    config=self.config,
                    password=password,
                )
            )

            if result == "authorized":
                self.status_label.setText("Logged in successfully.")
                self.accept()
                return

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Login error",
                str(exc),
            )
            self.status_label.setText("Could not complete two-step verification.")

        finally:
            self.set_busy(False)