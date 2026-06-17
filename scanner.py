import hashlib
from pathlib import Path

from telethon.errors import FloodWaitError

from database import Database
from models import IndexChannel
from telegram_service import TelegramService


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def iter_files(folder_path: Path):
    ignored_suffixes = {
        ".part",
        ".tmp",
        ".crdownload",
    }

    for path in folder_path.rglob("*"):
        if not path.is_file():
            continue

        if path.name.startswith("."):
            continue

        if path.suffix.lower() in ignored_suffixes:
            continue

        yield path


class FolderScanner:
    def __init__(
        self,
        root_folder: Path,
        database: Database,
        telegram_service: TelegramService,
        index_channel: IndexChannel,
    ):
        self.root_folder = root_folder
        self.database = database
        self.telegram_service = telegram_service
        self.index_channel = index_channel

    async def scan_once(self) -> None:
        if not self.root_folder.exists():
            raise FileNotFoundError(f"Root folder does not exist: {self.root_folder}")

        if not self.root_folder.is_dir():
            raise NotADirectoryError(f"Root path is not a folder: {self.root_folder}")

        subfolders = sorted(path for path in self.root_folder.iterdir() if path.is_dir())

        if not subfolders:
            print(f"[INFO] No subfolders found in {self.root_folder}")
            return

        for folder_path in subfolders:
            await self.upload_new_files_from_folder(folder_path)

    async def upload_new_files_from_folder(self, folder_path: Path) -> None:
        files = sorted(iter_files(folder_path))

        if not files:
            print(f"[EMPTY] No files found in {folder_path}")
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
                    print(f"[SKIP] Already uploaded: {file_path}")
                    continue

                relative_name = file_path.relative_to(folder_path)

                print(f"[UPLOAD] {file_path} -> {folder_channel.title}")

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

                print(f"[DONE] Uploaded: {file_path}")

            except FloodWaitError as exc:
                import asyncio

                print(f"[FLOOD WAIT] Telegram requested waiting {exc.seconds} seconds.")
                await asyncio.sleep(exc.seconds)

            except Exception as exc:
                print(f"[ERROR] Could not upload {file_path}: {exc}")