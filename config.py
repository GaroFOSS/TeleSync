import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_data_dir


APP_NAME = "TeleSync"
APP_AUTHOR = "GaroFOSS"


@dataclass
class AppConfig:
    api_id: int
    api_hash: str
    session_name: str
    scan_interval_seconds: int
    app_state_path: Path
    app_data_dir: Path


def get_app_data_dir() -> Path:
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_session_name(raw_session_name: str | None, app_data_dir: Path) -> str:
    """
    Telethon accepts a session name/path without the .session extension.

    If SESSION_NAME is relative, store it inside the app data directory.
    If SESSION_NAME is absolute, use it as-is.
    """
    if not raw_session_name:
        return str(app_data_dir / "folder_uploader")

    session_path = Path(raw_session_name).expanduser()

    if session_path.is_absolute():
        return str(session_path)

    return str(app_data_dir / raw_session_name)


def load_config() -> AppConfig:
    load_dotenv()

    api_id_raw = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    if not api_id_raw:
        raise ValueError("Missing API_ID in .env")

    if not api_hash:
        raise ValueError("Missing API_HASH in .env")

    app_data_dir = get_app_data_dir()

    app_state_raw = os.getenv("APP_STATE_PATH")
    if app_state_raw:
        app_state_path = Path(app_state_raw).expanduser()
        if not app_state_path.is_absolute():
            app_state_path = app_data_dir / app_state_path
    else:
        app_state_path = app_data_dir / "telesync_state.json"

    return AppConfig(
        api_id=int(api_id_raw),
        api_hash=api_hash,
        session_name=resolve_session_name(
            os.getenv("SESSION_NAME"),
            app_data_dir,
        ),
        scan_interval_seconds=int(os.getenv("SCAN_INTERVAL_SECONDS", "30")),
        app_state_path=app_state_path,
        app_data_dir=app_data_dir,
    )