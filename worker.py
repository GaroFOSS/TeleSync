import asyncio
import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from telethon import TelegramClient

from config import AppConfig
from database import Database
from scanner import FolderScanner
from telegram_service import TelegramService


class SyncWorker(QThread):
    log_message = Signal(str)
    folder_status = Signal(str, str)

    def __init__(
        self,
        config: AppConfig,
        main_folders: list[Path],
        recursive_channels: bool,
    ):
        super().__init__()
        self.config = config
        self.main_folders = main_folders
        self.recursive_channels = recursive_channels
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        try:
            asyncio.run(self.run_async())
        except Exception as exc:
            self.log_message.emit(f"[FATAL] {exc}")

    async def run_async(self) -> None:
        client = TelegramClient(
            self.config.session_name,
            self.config.api_id,
            self.config.api_hash,
        )

        await client.start()

        try:
            self.log_message.emit("[STARTED] TeleSync worker started.")

            while not self._stop_event.is_set():
                for main_folder in self.main_folders:
                    if self._stop_event.is_set():
                        break

                    await self.scan_main_folder(
                        client=client,
                        main_folder=main_folder,
                    )

                await self.sleep_with_stop(self.config.scan_interval_seconds)

        finally:
            await client.disconnect()
            self.log_message.emit("[STOPPED] TeleSync worker stopped.")

    async def scan_main_folder(
        self,
        client: TelegramClient,
        main_folder: Path,
    ) -> None:
        try:
            self.folder_status.emit(str(main_folder), "Preparing database")

            database = Database.for_main_folder(main_folder)
            database.init()

            telegram_service = TelegramService(
                client=client,
                database=database,
            )

            self.folder_status.emit(str(main_folder), "Preparing index channel")

            index_channel = await telegram_service.get_or_create_index_channel(
                main_folder=main_folder,
            )

            scanner = FolderScanner(
                main_folder=main_folder,
                database=database,
                telegram_service=telegram_service,
                index_channel=index_channel,
                log=self.log_message.emit,
                status=self.folder_status.emit,
                recursive_channels=self.recursive_channels,
            )

            await scanner.scan_once()

        except Exception as exc:
            self.folder_status.emit(str(main_folder), "Error")
            self.log_message.emit(f"[ERROR] {main_folder}: {exc}")

    async def sleep_with_stop(self, seconds: int) -> None:
        for _ in range(seconds):
            if self._stop_event.is_set():
                return

            await asyncio.sleep(1)