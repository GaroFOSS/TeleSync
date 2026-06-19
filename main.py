import asyncio
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from auth_service import is_authorized
from config import load_config
from gui import MainWindow
from login_dialog import LoginDialog


def main() -> None:
    app = QApplication(sys.argv)

    try:
        config = load_config()
    except Exception as exc:
        QMessageBox.critical(
            None,
            "Configuration error",
            str(exc),
        )
        sys.exit(1)

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