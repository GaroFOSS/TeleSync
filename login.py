import asyncio

from telethon import TelegramClient

from config import load_config


async def main() -> None:
    config = load_config()

    client = TelegramClient(
        config.session_name,
        config.api_id,
        config.api_hash,
    )

    await client.start()

    me = await client.get_me()

    print("Logged in successfully.")
    print(f"User: {me.first_name} ({me.id})")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())