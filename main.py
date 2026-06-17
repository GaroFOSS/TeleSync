import asyncio

from telethon import TelegramClient

from config import load_config
from database import Database
from scanner import FolderScanner
from telegram_service import TelegramService


async def main() -> None:
    config = load_config()

    database = Database(config.db_path)
    database.init()

    client = TelegramClient(
        config.session_name,
        config.api_id,
        config.api_hash,
    )

    async with client:
        print("[STARTED] Telegram folder uploader is running.")
        print(f"[ROOT] Watching: {config.root_folder}")

        telegram_service = TelegramService(
            client=client,
            database=database,
        )

        index_channel = await telegram_service.get_or_create_index_channel(
            title=config.index_channel_title,
        )

        print(f"[INDEX CHANNEL] Using: {index_channel.title}")

        scanner = FolderScanner(
            root_folder=config.root_folder,
            database=database,
            telegram_service=telegram_service,
            index_channel=index_channel,
        )

        while True:
            await scanner.scan_once()
            await asyncio.sleep(config.scan_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())