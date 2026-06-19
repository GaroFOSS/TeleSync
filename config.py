import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class AppConfig:
    api_id: int
    api_hash: str
    session_name: str
    scan_interval_seconds: int
    app_state_path: Path


def load_config() -> AppConfig:
    load_dotenv()

    api_id_raw = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    if not api_id_raw:
        raise ValueError("Missing API_ID in .env")

    if not api_hash:
        raise ValueError("Missing API_HASH in .env")

    return AppConfig(
        api_id=int(api_id_raw),
        api_hash=api_hash,
        session_name=os.getenv("SESSION_NAME", "folder_uploader"),
        scan_interval_seconds=int(os.getenv("SCAN_INTERVAL_SECONDS", "30")),
        app_state_path=Path(os.getenv("APP_STATE_PATH", "telesync_state.json")).resolve(),
    )