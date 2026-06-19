from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app_state import AppState
from config import AppConfig
from database import Database
from worker import SyncWorker


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig):
        super().__init__()

        self.config = config
        self.state = AppState(config.app_state_path)
        self.worker: Optional[SyncWorker] = None

        self.setWindowTitle("TeleSync")
        self.resize(1000, 650)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            [
                "Main Folder",
                "Database Location",
                "Status",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.add_button = QPushButton("Add Main Folder")
        self.remove_button = QPushButton("Remove Selected")
        self.start_button = QPushButton("Start Sync")
        self.stop_button = QPushButton("Stop Sync")

        self.stop_button.setEnabled(False)

        self.add_button.clicked.connect(self.add_main_folder)
        self.remove_button.clicked.connect(self.remove_selected_folder)
        self.start_button.clicked.connect(self.start_sync)
        self.stop_button.clicked.connect(self.stop_sync)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.log_box)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.refresh_table()

    def refresh_table(self) -> None:
        self.table.setRowCount(0)

        for folder in self.state.main_folders:
            row = self.table.rowCount()
            self.table.insertRow(row)

            folder_path = Path(folder)
            database_path = Database.for_main_folder(folder_path).db_path

            self.table.setItem(row, 0, QTableWidgetItem(str(folder_path)))
            self.table.setItem(row, 1, QTableWidgetItem(str(database_path)))
            self.table.setItem(row, 2, QTableWidgetItem("Stopped"))

    def add_main_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose a main folder",
            str(Path.home()),
        )

        if not folder:
            return

        self.state.add_main_folder(Path(folder))
        self.refresh_table()
        self.append_log(f"[ADDED] {folder}")

    def remove_selected_folder(self) -> None:
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No folder selected",
                "Select a main folder first.",
            )
            return

        folder_item = self.table.item(selected_row, 0)

        if folder_item is None:
            return

        folder = folder_item.text()

        self.state.remove_main_folder(folder)
        self.refresh_table()
        self.append_log(f"[REMOVED] {folder}")

    def start_sync(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(
                self,
                "Already running",
                "TeleSync is already running.",
            )
            return

        if not self.state.main_folders:
            QMessageBox.warning(
                self,
                "No folders",
                "Add at least one main folder first.",
            )
            return

        main_folders = [
            Path(folder).expanduser().resolve()
            for folder in self.state.main_folders
        ]

        self.worker = SyncWorker(
            config=self.config,
            main_folders=main_folders,
        )

        self.worker.log_message.connect(self.append_log)
        self.worker.folder_status.connect(self.update_folder_status)
        self.worker.finished.connect(self.on_worker_finished)

        self.worker.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.add_button.setEnabled(False)
        self.remove_button.setEnabled(False)

        self.append_log("[GUI] Sync started.")

    def stop_sync(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.append_log("[GUI] Stopping sync...")

        self.stop_button.setEnabled(False)

    def on_worker_finished(self) -> None:
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.add_button.setEnabled(True)
        self.remove_button.setEnabled(True)

        self.update_all_statuses("Stopped")

    def update_folder_status(self, folder: str, status: str) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)

            if item is not None and item.text() == folder:
                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, status_item)
                return

    def update_all_statuses(self, status: str) -> None:
        for row in range(self.table.rowCount()):
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, status_item)

    def append_log(self, message: str) -> None:
        self.log_box.appendPlainText(message)

    def closeEvent(self, event) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)

        event.accept()