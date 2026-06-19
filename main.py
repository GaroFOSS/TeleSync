import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from config import load_config
from gui import MainWindow


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
        return

    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()