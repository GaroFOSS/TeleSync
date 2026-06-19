import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Optional

from models import FolderChannel, IndexChannel


def hide_folder_on_windows(folder: Path) -> None:
    if os.name != "nt":
        return

    try:
        subprocess.run(
            ["attrib", "+h", str(folder)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    @classmethod
    def for_main_folder(cls, main_folder: Path) -> "Database":
        main_folder = main_folder.expanduser().resolve()

        telesync_dir = main_folder / ".telesync"
        telesync_dir.mkdir(parents=True, exist_ok=True)

        hide_folder_on_windows(telesync_dir)

        return cls(telesync_dir / "telesync.db")

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS index_channel (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    title TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    access_hash INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS folder_channels (
                    folder_path TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    access_hash INTEGER NOT NULL,
                    invite_link TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_path TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    telegram_message_id INTEGER,
                    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(folder_path, file_hash)
                )
                """
            )

            conn.commit()

    def get_index_channel(self) -> Optional[IndexChannel]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT title, channel_id, access_hash
                FROM index_channel
                WHERE id = 1
                """
            ).fetchone()

        if not row:
            return None

        return IndexChannel(
            title=row[0],
            channel_id=row[1],
            access_hash=row[2],
        )

    def save_index_channel(self, channel: IndexChannel) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO index_channel
                (id, title, channel_id, access_hash)
                VALUES (1, ?, ?, ?)
                """,
                (
                    channel.title,
                    channel.channel_id,
                    channel.access_hash,
                ),
            )

            conn.commit()

    def get_folder_channel(self, folder_path: Path) -> Optional[FolderChannel]:
        normalized_path = str(folder_path.expanduser().resolve())

        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT folder_path, title, channel_id, access_hash, invite_link
                FROM folder_channels
                WHERE folder_path = ?
                """,
                (normalized_path,),
            ).fetchone()

        if not row:
            return None

        return FolderChannel(
            folder_path=row[0],
            title=row[1],
            channel_id=row[2],
            access_hash=row[3],
            invite_link=row[4],
        )

    def save_folder_channel(self, channel: FolderChannel) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO folder_channels
                (folder_path, title, channel_id, access_hash, invite_link)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    channel.folder_path,
                    channel.title,
                    channel.channel_id,
                    channel.access_hash,
                    channel.invite_link,
                ),
            )

            conn.commit()

    def is_file_uploaded(self, folder_path: Path, file_hash: str) -> bool:
        normalized_path = str(folder_path.expanduser().resolve())

        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM uploaded_files
                WHERE folder_path = ?
                  AND file_hash = ?
                """,
                (
                    normalized_path,
                    file_hash,
                ),
            ).fetchone()

        return row is not None

    def save_uploaded_file(
        self,
        folder_path: Path,
        file_path: Path,
        file_hash: str,
        file_size: int,
        telegram_message_id: Optional[int],
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO uploaded_files
                (folder_path, file_path, file_hash, file_size, telegram_message_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(folder_path.expanduser().resolve()),
                    str(file_path.expanduser().resolve()),
                    file_hash,
                    file_size,
                    telegram_message_id,
                ),
            )

            conn.commit()