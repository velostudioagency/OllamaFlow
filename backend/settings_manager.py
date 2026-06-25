import json
from pathlib import Path
from typing import Dict, Optional


class SettingsManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.data_dir / "settings.json"
        self.settings = self._load()

    def _load(self) -> Dict:
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "ollama_base": "http://localhost:11434",
            "default_model": "llama3.1:8b",
            "groq_api_key": "",
            "groq_model": "llama-3.3-70b-versatile",
            "provider": "ollama",
        }

    def _save(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def get_all(self) -> Dict:
        return self.settings.copy()

    def update(self, data: Dict) -> str:
        self.settings.update(data)
        self._save()
        return "Settings updated."

    def get_groq_key(self) -> str:
        return self.settings.get("groq_api_key", "")

    def get_provider(self) -> str:
        return self.settings.get("provider", "ollama")


settings_manager = SettingsManager()
