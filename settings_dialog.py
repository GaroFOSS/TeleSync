# SPDX-License-Identifier: GPL-3.0-or-later

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from config import EnvSettings, save_env_settings, validate_env_settings


class SettingsDialog(QDialog):
    def __init__(self, settings: EnvSettings, parent=None):
        super().__init__(parent)

        self.settings = settings

        self.setWindowTitle("TeleSync Settings")
        self.setMinimumWidth(560)
        self.setModal(True)

        title = QLabel("Telegram API Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        info = QLabel(
            "Enter your Telegram API credentials. You can get them from "
            "https://my.telegram.org under API development tools."
        )
        info.setWordWrap(True)

        env_path_label = QLabel(f"Settings file:\n{settings.env_path}")
        env_path_label.setWordWrap(True)

        self.api_id_input = QLineEdit()
        self.api_id_input.setPlaceholderText("Example: 12345678")
        self.api_id_input.setText(settings.api_id)

        self.api_hash_input = QLineEdit()
        self.api_hash_input.setPlaceholderText("Paste your API_HASH here")
        self.api_hash_input.setText(settings.api_hash)
        self.api_hash_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.show_hash_checkbox = QCheckBox("Show API_HASH")
        self.show_hash_checkbox.stateChanged.connect(self.toggle_api_hash_visibility)

        self.session_name_input = QLineEdit()
        self.session_name_input.setText(settings.session_name or "folder_uploader")

        self.scan_interval_input = QLineEdit()
        self.scan_interval_input.setText(settings.scan_interval_seconds or "30")

        self.app_state_path_input = QLineEdit()
        self.app_state_path_input.setText(settings.app_state_path or "telesync_state.json")

        form = QFormLayout()
        form.addRow("API_ID:", self.api_id_input)
        form.addRow("API_HASH:", self.api_hash_input)
        form.addRow("", self.show_hash_checkbox)
        form.addRow("Session name:", self.session_name_input)
        form.addRow("Scan interval seconds:", self.scan_interval_input)
        form.addRow("App state path:", self.app_state_path_input)

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(info)
        layout.addSpacing(8)
        layout.addWidget(env_path_label)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def toggle_api_hash_visibility(self) -> None:
        if self.show_hash_checkbox.isChecked():
            self.api_hash_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_hash_input.setEchoMode(QLineEdit.EchoMode.Password)

    def save_settings(self) -> None:
        new_settings = EnvSettings(
            env_path=self.settings.env_path,
            api_id=self.api_id_input.text().strip(),
            api_hash=self.api_hash_input.text().strip(),
            session_name=self.session_name_input.text().strip() or "folder_uploader",
            scan_interval_seconds=self.scan_interval_input.text().strip() or "30",
            app_state_path=self.app_state_path_input.text().strip() or "telesync_state.json",
        )

        errors = validate_env_settings(new_settings)

        if errors:
            QMessageBox.warning(
                self,
                "Invalid settings",
                "\n".join(errors),
            )
            return

        save_env_settings(new_settings)

        self.settings = new_settings

        QMessageBox.information(
            self,
            "Settings saved",
            "TeleSync settings were saved successfully.",
        )

        self.accept()