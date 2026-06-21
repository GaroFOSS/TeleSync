# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from auth_service import is_authorized
from config import load_config, load_env_settings
from gui import MainWindow
from login_dialog import LoginDialog
from settings_dialog import SettingsDialog


def get_valid_config_or_open_settings(app: QApplication):
    while True:
        try:
            return load_config()

        except Exception as exc:
            settings = load_env_settings()

            QMessageBox.warning(
                None,
                "TeleSync settings required",
                (
                    "TeleSync needs your Telegram API settings before it can start.\n\n"
                    f"{exc}"
                ),
            )

            dialog = SettingsDialog(settings)

            if dialog.exec() != SettingsDialog.DialogCode.Accepted:
                sys.exit(0)


def main() -> None:
    app = QApplication(sys.argv)

    config = get_valid_config_or_open_settings(app)

    try:
        already_logged_in = asyncio.run(is_authorized(config))
    except Exception as exc:
        QMessageBox.critical(
            None,
            "Telegram connection error",
            str(exc),
        )
        sys.exit(1)

    if not already_logged_in:
        login_dialog = LoginDialog(config)

        if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
            sys.exit(0)

    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()