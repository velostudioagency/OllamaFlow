import json
import os
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
            "search_provider": "auto",
            "brave_api_key": "",
            "searxng_url": "",
            "cors_origins": "http://localhost:5173,http://localhost:3000",
            "api_token": "",
            "browser_path": "",
            "firecrawl_url": "http://localhost:3001",
            "firecrawl_api_key": "",
            "firecrawl_mode": "self_hosted",
        }

    def _save(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)

    def get(self, key: str, default=None):
        val = self.settings.get(key, default)
        if not val:
            env_key = f"OLLAMAFLOW_{key.upper()}"
            env_val = os.environ.get(env_key, "")
            if env_val:
                return env_val
        return val

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

    def get_search_settings(self) -> Dict:
        return {
            "search_provider": self.settings.get("search_provider", "auto"),
            "brave_api_key": self.settings.get("brave_api_key", ""),
            "searxng_url": self.settings.get("searxng_url", ""),
        }


settings_manager = SettingsManager()
