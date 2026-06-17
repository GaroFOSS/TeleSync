import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class AppConfig:
    api_id: int
    api_hash: str
    session_name: str
    root_folder: Path
    scan_interval_seconds: int
    index_channel_title: str
    db_path: str


def load_config() -> AppConfig:
    load_dotenv()

    api_id_raw = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    root_folder_raw = os.getenv("ROOT_FOLDER")

    if not api_id_raw:
        raise ValueError("Missing API_ID in .env")

    if not api_hash:
        raise ValueError("Missing API_HASH in .env")

    if not root_folder_raw:
        raise ValueError("Missing ROOT_FOLDER in .env")

    return AppConfig(
        api_id=int(api_id_raw),
        api_hash=api_hash,
        session_name=os.getenv("SESSION_NAME", "folder_uploader"),
        root_folder=Path(root_folder_raw).expanduser().resolve(),
        scan_interval_seconds=int(os.getenv("SCAN_INTERVAL_SECONDS", "30")),
        index_channel_title=os.getenv("INDEX_CHANNEL_TITLE", "Folder Upload Index"),
        db_path=os.getenv("DB_PATH", "telegram_uploads.db"),
    )