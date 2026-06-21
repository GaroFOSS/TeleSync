import json
from pathlib import Path


class AppState:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.main_folders: list[str] = []
        self.recursive_channels: bool = False
        self.load()

    def load(self) -> None:
        if not self.state_path.exists():
            self.main_folders = []
            self.recursive_channels = False
            return

        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.main_folders = data.get("main_folders", [])
            self.recursive_channels = bool(data.get("recursive_channels", False))
        except Exception:
            self.main_folders = []
            self.recursive_channels = False

    def save(self) -> None:
        data = {
            "main_folders": self.main_folders,
            "recursive_channels": self.recursive_channels,
        }

        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        self.state_path.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_main_folder(self, folder: Path) -> None:
        normalized = str(folder.expanduser().resolve())

        if normalized not in self.main_folders:
            self.main_folders.append(normalized)
            self.save()

    def remove_main_folder(self, folder: str) -> None:
        normalized = str(Path(folder).expanduser().resolve())

        self.main_folders = [
            existing for existing in self.main_folders
            if str(Path(existing).expanduser().resolve()) != normalized
        ]

        self.save()

    def set_recursive_channels(self, enabled: bool) -> None:
        self.recursive_channels = enabled
        self.save()