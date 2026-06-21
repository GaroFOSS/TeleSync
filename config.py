# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from platformdirs import user_data_dir


APP_NAME = "TeleSync"
APP_AUTHOR = "GaroFOSS"


@dataclass
class EnvSettings:
    env_path: Path
    api_id: str
    api_hash: str
    session_name: str
    scan_interval_seconds: str
    app_state_path: str


@dataclass
class AppConfig:
    api_id: int
    api_hash: str
    session_name: str
    scan_interval_seconds: int
    app_state_path: Path
    app_data_dir: Path
    env_path: Path


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def get_app_data_dir() -> Path:
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_env_content() -> str:
    return (
        "# TeleSync settings\n"
        "# Get API_ID and API_HASH from https://my.telegram.org\n\n"
        "API_ID=\n"
        "API_HASH=\n\n"
        "SESSION_NAME=folder_uploader\n"
        "SCAN_INTERVAL_SECONDS=30\n"
        "APP_STATE_PATH=telesync_state.json\n"
    )


def find_or_create_env_file() -> Path:
    app_dir = get_app_dir()
    app_data_dir = get_app_data_dir()

    local_env = app_dir / ".env"
    app_data_env = app_data_dir / ".env"

    if local_env.exists():
        return local_env

    if app_data_env.exists():
        return app_data_env

    app_data_env.parent.mkdir(parents=True, exist_ok=True)
    app_data_env.write_text(default_env_content(), encoding="utf-8")

    return app_data_env


def load_env_settings() -> EnvSettings:
    env_path = find_or_create_env_file()
    values = dotenv_values(env_path)

    return EnvSettings(
        env_path=env_path,
        api_id=str(values.get("API_ID") or "").strip(),
        api_hash=str(values.get("API_HASH") or "").strip(),
        session_name=str(values.get("SESSION_NAME") or "folder_uploader").strip(),
        scan_interval_seconds=str(values.get("SCAN_INTERVAL_SECONDS") or "30").strip(),
        app_state_path=str(values.get("APP_STATE_PATH") or "telesync_state.json").strip(),
    )


def escape_env_value(value: str) -> str:
    value = value.strip()

    if not value:
        return ""

    if any(char.isspace() for char in value) or "#" in value:
        value = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{value}"'

    return value


def save_env_settings(settings: EnvSettings) -> None:
    settings.env_path.parent.mkdir(parents=True, exist_ok=True)

    content = (
        "# TeleSync settings\n"
        "# Get API_ID and API_HASH from https://my.telegram.org\n\n"
        f"API_ID={escape_env_value(settings.api_id)}\n"
        f"API_HASH={escape_env_value(settings.api_hash)}\n\n"
        f"SESSION_NAME={escape_env_value(settings.session_name or 'folder_uploader')}\n"
        f"SCAN_INTERVAL_SECONDS={escape_env_value(settings.scan_interval_seconds or '30')}\n"
        f"APP_STATE_PATH={escape_env_value(settings.app_state_path or 'telesync_state.json')}\n"
    )

    settings.env_path.write_text(content, encoding="utf-8")


def resolve_session_name(raw_session_name: str | None, app_data_dir: Path) -> str:
    if not raw_session_name:
        return str(app_data_dir / "folder_uploader")

    session_path = Path(raw_session_name).expanduser()

    if session_path.is_absolute():
        return str(session_path)

    return str(app_data_dir / raw_session_name)


def resolve_app_state_path(raw_app_state_path: str | None, app_data_dir: Path) -> Path:
    if not raw_app_state_path:
        return app_data_dir / "telesync_state.json"

    app_state_path = Path(raw_app_state_path).expanduser()

    if app_state_path.is_absolute():
        return app_state_path

    return app_data_dir / app_state_path


def validate_env_settings(settings: EnvSettings) -> list[str]:
    errors: list[str] = []

    if not settings.api_id:
        errors.append("API_ID is required.")

    elif not settings.api_id.isdigit():
        errors.append("API_ID must be a number.")

    if not settings.api_hash:
        errors.append("API_HASH is required.")

    try:
        interval = int(settings.scan_interval_seconds)
        if interval <= 0:
            errors.append("SCAN_INTERVAL_SECONDS must be greater than zero.")
    except ValueError:
        errors.append("SCAN_INTERVAL_SECONDS must be a number.")

    return errors


def load_config() -> AppConfig:
    settings = load_env_settings()
    errors = validate_env_settings(settings)

    if errors:
        raise ValueError("\n".join(errors))

    app_data_dir = get_app_data_dir()

    load_dotenv(settings.env_path, override=True)

    return AppConfig(
        api_id=int(settings.api_id),
        api_hash=settings.api_hash,
        session_name=resolve_session_name(
            settings.session_name,
            app_data_dir,
        ),
        scan_interval_seconds=int(settings.scan_interval_seconds),
        app_state_path=resolve_app_state_path(
            settings.app_state_path,
            app_data_dir,
        ),
        app_data_dir=app_data_dir,
        env_path=settings.env_path,
    )