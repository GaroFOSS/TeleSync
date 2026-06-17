from dataclasses import dataclass
from typing import Optional


@dataclass
class FolderChannel:
    folder_path: str
    title: str
    channel_id: int
    access_hash: int
    invite_link: Optional[str]


@dataclass
class IndexChannel:
    title: str
    channel_id: int
    access_hash: int