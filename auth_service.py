from dataclasses import dataclass
from typing import Optional

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
)

from config import AppConfig


@dataclass
class LoginCodeResult:
    phone_code_hash: str


async def is_authorized(config: AppConfig) -> bool:
    client = TelegramClient(
        config.session_name,
        config.api_id,
        config.api_hash,
    )

    await client.connect()

    try:
        return await client.is_user_authorized()
    finally:
        await client.disconnect()


async def request_login_code(
    config: AppConfig,
    phone: str,
) -> LoginCodeResult:
    client = TelegramClient(
        config.session_name,
        config.api_id,
        config.api_hash,
    )

    await client.connect()

    try:
        if await client.is_user_authorized():
            return LoginCodeResult(phone_code_hash="")

        sent_code = await client.send_code_request(phone)

        return LoginCodeResult(
            phone_code_hash=sent_code.phone_code_hash,
        )

    except PhoneNumberInvalidError as exc:
        raise ValueError("Invalid phone number. Use international format, for example +5511999999999.") from exc

    except FloodWaitError as exc:
        raise RuntimeError(f"Telegram requested a wait of {exc.seconds} seconds before trying again.") from exc

    finally:
        await client.disconnect()


async def complete_login_with_code(
    config: AppConfig,
    phone: str,
    code: str,
    phone_code_hash: str,
) -> str:
    """
    Returns:
        "authorized" if login completed.
        "2fa_required" if Telegram needs the account password.
    """
    client = TelegramClient(
        config.session_name,
        config.api_id,
        config.api_hash,
    )

    await client.connect()

    try:
        if await client.is_user_authorized():
            return "authorized"

        await client.sign_in(
            phone=phone,
            code=code,
            phone_code_hash=phone_code_hash,
        )

        return "authorized"

    except SessionPasswordNeededError:
        return "2fa_required"

    except PhoneCodeInvalidError as exc:
        raise ValueError("Invalid Telegram login code.") from exc

    except PhoneCodeExpiredError as exc:
        raise ValueError("The Telegram login code expired. Request a new code.") from exc

    finally:
        await client.disconnect()


async def complete_login_with_password(
    config: AppConfig,
    password: str,
) -> str:
    client = TelegramClient(
        config.session_name,
        config.api_id,
        config.api_hash,
    )

    await client.connect()

    try:
        if await client.is_user_authorized():
            return "authorized"

        await client.sign_in(password=password)

        return "authorized"

    finally:
        await client.disconnect()