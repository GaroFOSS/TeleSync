import json
from pathlib import Path


class AppState:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.main_folders: list[str] = []
        self.load()

    def load(self) -> None:
        if not self.state_path.exists():
            self.main_folders = []
            return

        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.main_folders = data.get("main_folders", [])
        except Exception:
            self.main_folders = []

    def save(self) -> None:
        data = {
            "main_folders": self.main_folders,
        }

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