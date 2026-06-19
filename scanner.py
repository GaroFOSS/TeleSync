import asyncio
import hashlib
from pathlib import Path
from typing import Callable

from telethon.errors import FloodWaitError

from database import Database
from models import IndexChannel
from telegram_service import TelegramService


LogCallback = Callable[[str], None]
StatusCallback = Callable[[str, str], None]


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def should_ignore_path(path: Path) -> bool:
    ignored_suffixes = {
        ".part",
        ".tmp",
        ".crdownload",
    }

    if path.name.startswith("."):
        return True

    if path.suffix.lower() in ignored_suffixes:
        return True

    if ".telesync" in path.parts:
        return True

    return False


def iter_files(folder_path: Path):
    for path in folder_path.rglob("*"):
        if not path.is_file():
            continue

        relative_parts = path.relative_to(folder_path).parts

        if any(part.startswith(".") for part in relative_parts):
            continue

        if should_ignore_path(path):
            continue

        yield path


class FolderScanner:
    def __init__(
        self,
        main_folder: Path,
        database: Database,
        telegram_service: TelegramService,
        index_channel: IndexChannel,
        log: LogCallback,
        status: StatusCallback,
    ):
        self.main_folder = main_folder
        self.database = database
        self.telegram_service = telegram_service
        self.index_channel = index_channel
        self.log = log
        self.status = status

    async def scan_once(self) -> None:
        if not self.main_folder.exists():
            raise FileNotFoundError(f"Main folder does not exist: {self.main_folder}")

        if not self.main_folder.is_dir():
            raise NotADirectoryError(f"Main folder path is not a directory: {self.main_folder}")

        self.status(str(self.main_folder), "Scanning")

        subfolders = sorted(
            path for path in self.main_folder.iterdir()
            if path.is_dir()
            and path.name != ".telesync"
            and not path.name.startswith(".")
        )

        if not subfolders:
            self.log(f"[INFO] No subfolders found in {self.main_folder}")
            self.status(str(self.main_folder), "No subfolders")
            return

        for folder_path in subfolders:
            await self.upload_new_files_from_folder(folder_path)

        self.status(str(self.main_folder), "Waiting")

    async def upload_new_files_from_folder(self, folder_path: Path) -> None:
        files = sorted(iter_files(folder_path))

        if not files:
            self.log(f"[EMPTY] No files found in {folder_path}")
            return

        folder_channel = await self.telegram_service.get_or_create_folder_channel(
            folder_path=folder_path,
            index_channel=self.index_channel,
        )

        for file_path in files:
            try:
                file_size = file_path.stat().st_size
                file_hash = file_sha256(file_path)

                if self.database.is_file_uploaded(folder_path, file_hash):
                    self.log(f"[SKIP] Already uploaded: {file_path}")
                    continue

                relative_name = file_path.relative_to(folder_path)

                self.log(f"[UPLOAD] {file_path} -> {folder_channel.title}")

                message = await self.telegram_service.send_file_to_folder_channel(
                    folder_channel=folder_channel,
                    file_path=file_path,
                    caption=str(relative_name),
                )

                self.database.save_uploaded_file(
                    folder_path=folder_path,
                    file_path=file_path,
                    file_hash=file_hash,
                    file_size=file_size,
                    telegram_message_id=message.id if message else None,
                )

                self.log(f"[DONE] Uploaded: {file_path}")

            except FloodWaitError as exc:
                self.log(f"[FLOOD WAIT] Telegram requested waiting {exc.seconds} seconds.")
                await asyncio.sleep(exc.seconds)

            except Exception as exc:
                self.log(f"[ERROR] Could not upload {file_path}: {exc}")