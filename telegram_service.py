import re
from pathlib import Path
from typing import Optional, cast

from telethon import TelegramClient, functions
from telethon.tl.types import InputPeerChannel, Updates, Channel

from database import Database
from models import FolderChannel, IndexChannel


def normalize_title(name: str) -> str:
    title = re.sub(r"\s+", " ", name).strip()
    return title[:120] or "Uploaded Folder"


class TelegramService:
    def __init__(self, client: TelegramClient, database: Database):
        self.client = client
        self.database = database

    async def get_or_create_index_channel(self, title: str) -> IndexChannel:
        existing = self.database.get_index_channel()

        if existing:
            return existing

        result = await self.client(
            functions.channels.CreateChannelRequest(
                title=title,
                about="Index channel for automatically created folder upload channels.",
                broadcast=True,
            )
        )

        channel = result.chats[0]

        index_channel = IndexChannel(
            title=title,
            channel_id=channel.id,
            access_hash=channel.access_hash,
        )

        self.database.save_index_channel(index_channel)

        await self.send_message_to_channel(
            channel=index_channel,
            message=(
                "📌 **Folder upload index channel created.**\n\n"
                "Every new folder channel created by the uploader will be posted here."
            ),
        )

        print(f"[NEW INDEX CHANNEL] Created '{title}'")

        return index_channel

    async def get_or_create_folder_channel(
        self,
        folder_path: Path,
        index_channel: IndexChannel,
    ) -> FolderChannel:
        existing = self.database.get_folder_channel(folder_path)

        if existing:
            return existing

        return await self.create_folder_channel(
            folder_path=folder_path,
            index_channel=index_channel,
        )

    async def create_folder_channel(
        self,
        folder_path: Path,
        index_channel: IndexChannel,
    ) -> FolderChannel:
        title = normalize_title(folder_path.name)

        result = await self.client(
            functions.channels.CreateChannelRequest(
                title=title,
                about=f"Automatic upload channel for folder: {folder_path}",
                broadcast=True,
            )
        )

        telegram_channel = result.chats[0]

        invite_link = await self.export_invite_link(
            channel_id=telegram_channel.id,
            access_hash=telegram_channel.access_hash,
        )

        folder_channel = FolderChannel(
            folder_path=str(folder_path.resolve()),
            title=title,
            channel_id=telegram_channel.id,
            access_hash=telegram_channel.access_hash,
            invite_link=invite_link,
        )

        self.database.save_folder_channel(folder_channel)

        await self.notify_index_channel_about_folder_channel(
            index_channel=index_channel,
            folder_path=folder_path,
            folder_channel=folder_channel,
        )

        print(f"[NEW CHANNEL] Created '{title}' for {folder_path}")

        if invite_link:
            print(f"[INVITE LINK] {invite_link}")

        return folder_channel

    async def export_invite_link(
        self,
        channel_id: int,
        access_hash: int,
    ) -> Optional[str]:
        peer = InputPeerChannel(
            channel_id=channel_id,
            access_hash=access_hash,
        )

        invite = await self.client(
            functions.messages.ExportChatInviteRequest(
                peer=peer,
            )
        )

        return getattr(invite, "link", None)

    async def notify_index_channel_about_folder_channel(
        self,
        index_channel: IndexChannel,
        folder_path: Path,
        folder_channel: FolderChannel,
    ) -> None:
        if folder_channel.invite_link:
            message = (
                "📢 **New folder channel created**\n\n"
                f"**Folder name:** `{folder_path.name}`\n"
                f"**Folder path:** `{folder_path.resolve()}`\n"
                f"**Telegram channel:** {folder_channel.title}\n"
                f"**Invite link:** {folder_channel.invite_link}"
            )
        else:
            message = (
                "📢 **New folder channel created**\n\n"
                f"**Folder name:** `{folder_path.name}`\n"
                f"**Folder path:** `{folder_path.resolve()}`\n"
                f"**Telegram channel:** {folder_channel.title}\n\n"
                "⚠️ Could not generate an invite link automatically."
            )

        await self.send_message_to_channel(
            channel=index_channel,
            message=message,
        )

    async def send_message_to_channel(
        self,
        channel: IndexChannel | FolderChannel,
        message: str,
    ) -> None:
        peer = InputPeerChannel(
            channel_id=channel.channel_id,
            access_hash=channel.access_hash,
        )

        await self.client.send_message(peer, message)

    async def send_file_to_folder_channel(
        self,
        folder_channel: FolderChannel,
        file_path: Path,
        caption: str,
    ):
        peer = InputPeerChannel(
            channel_id=folder_channel.channel_id,
            access_hash=folder_channel.access_hash,
        )

        return await self.client.send_file(
            peer,
            file=file_path,
            caption=caption,
            force_document=True,
        )