import asyncio
import hashlib
from pathlib import Path
from typing import Callable

from telethon.errors import FloodWaitError

from database import Database
from models import FolderChannel, IndexChannel
from telegram_service import TelegramNotificationTarget, TelegramService


LogCallback = Callable[[str], None]
StatusCallback = Callable[[str, str], None]


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def is_ignored_name(name: str) -> bool:
    return name.startswith(".") or name == ".telesync"


def is_ignored_file(path: Path, root: Path) -> bool:
    ignored_suffixes = {
        ".part",
        ".tmp",
        ".crdownload",
    }

    relative_parts = path.relative_to(root).parts

    if any(is_ignored_name(part) for part in relative_parts):
        return True

    if path.suffix.lower() in ignored_suffixes:
        return True

    return False


def iter_direct_subfolders(folder_path: Path):
    for path in folder_path.iterdir():
        if not path.is_dir():
            continue

        if is_ignored_name(path.name):
            continue

        yield path


def iter_direct_files(folder_path: Path):
    for path in folder_path.iterdir():
        if not path.is_file():
            continue

        if is_ignored_file(path, folder_path):
            continue

        yield path


def iter_recursive_files(folder_path: Path):
    for path in folder_path.rglob("*"):
        if not path.is_file():
            continue

        if is_ignored_file(path, folder_path):
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
        recursive_channels: bool = False,
    ):
        self.main_folder = main_folder
        self.database = database
        self.telegram_service = telegram_service
        self.index_channel = index_channel
        self.log = log
        self.status = status
        self.recursive_channels = recursive_channels

    async def scan_once(self) -> None:
        if not self.main_folder.exists():
            raise FileNotFoundError(f"Main folder does not exist: {self.main_folder}")

        if not self.main_folder.is_dir():
            raise NotADirectoryError(f"Main folder path is not a directory: {self.main_folder}")

        mode = "Recursive" if self.recursive_channels else "Top-level only"

        self.status(str(self.main_folder), f"Scanning ({mode})")
        self.log(f"[SCAN] {self.main_folder} | Mode: {mode}")

        top_level_folders = sorted(iter_direct_subfolders(self.main_folder))

        if not top_level_folders:
            self.log(f"[INFO] No subfolders found in {self.main_folder}")
            self.status(str(self.main_folder), "No subfolders")
            return

        if self.recursive_channels:
            for folder_path in top_level_folders:
                await self.sync_folder_recursive(
                    folder_path=folder_path,
                    notification_channel=self.index_channel,
                )
        else:
            for folder_path in top_level_folders:
                await self.sync_folder_current_behavior(folder_path)

        self.status(str(self.main_folder), "Waiting")

    async def sync_folder_current_behavior(self, folder_path: Path) -> None:
        """
        Current behavior:
        - One channel for each direct child of the main folder.
        - Files from nested subfolders are uploaded to that same top-level channel.
        """
        files = sorted(iter_recursive_files(folder_path))

        if not files:
            self.log(f"[EMPTY] No files found in {folder_path}")
            return

        folder_channel = await self.telegram_service.get_or_create_folder_channel(
            folder_path=folder_path,
            notification_channel=self.index_channel,
        )

        await self.upload_files_to_channel(
            folder_path=folder_path,
            folder_channel=folder_channel,
            files=files,
            relative_root=folder_path,
        )

    async def sync_folder_recursive(
        self,
        folder_path: Path,
        notification_channel: TelegramNotificationTarget,
    ) -> None:
        """
        Recursive behavior:
        - Every folder gets its own channel.
        - A top-level folder link is sent to the index channel.
        - A nested folder link is sent to its parent folder channel.
        - Files directly inside a folder are uploaded to that folder's own channel.
        """
        direct_files = sorted(iter_direct_files(folder_path))
        child_folders = sorted(iter_direct_subfolders(folder_path))

        if not direct_files and not child_folders:
            self.log(f"[EMPTY] No files or subfolders found in {folder_path}")
            return

        folder_channel = await self.telegram_service.get_or_create_folder_channel(
            folder_path=folder_path,
            notification_channel=notification_channel,
        )

        await self.upload_files_to_channel(
            folder_path=folder_path,
            folder_channel=folder_channel,
            files=direct_files,
            relative_root=folder_path,
        )

        for child_folder in child_folders:
            await self.sync_folder_recursive(
                folder_path=child_folder,
                notification_channel=folder_channel,
            )

    async def upload_files_to_channel(
        self,
        folder_path: Path,
        folder_channel: FolderChannel,
        files: list[Path],
        relative_root: Path,
    ) -> None:
        for file_path in files:
            try:
                file_size = file_path.stat().st_size
                file_hash = file_sha256(file_path)

                if self.database.is_file_uploaded(folder_path, file_hash):
                    self.log(f"[SKIP] Already uploaded: {file_path}")
                    continue

                relative_name = file_path.relative_to(relative_root)

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