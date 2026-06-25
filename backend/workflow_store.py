import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class WorkflowStore:
    def __init__(self, data_dir: str = "data/workflows"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _safe_filename(self, name: str) -> str:
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        return safe[:100]

    def save(self, name: str, workflow: Dict) -> str:
        filename = self._safe_filename(name) + ".json"
        filepath = self.data_dir / filename
        workflow["name"] = name
        workflow["saved_at"] = datetime.now().isoformat()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2, default=str)
        return f"Workflow '{name}' saved successfully."

    def load(self, name: str) -> Optional[Dict]:
        filename = self._safe_filename(name) + ".json"
        filepath = self.data_dir / filename
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_workflows(self) -> List[Dict]:
        workflows = []
        for filepath in self.data_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                workflows.append({
                    "name": data.get("name", filepath.stem),
                    "saved_at": data.get("saved_at", "Unknown"),
                    "node_count": len(data.get("nodes", []))
                })
            except Exception:
                workflows.append({
                    "name": filepath.stem,
                    "saved_at": "Error loading",
                    "node_count": 0
                })
        return sorted(workflows, key=lambda x: x.get("saved_at", ""), reverse=True)

    def delete(self, name: str) -> str:
        filename = self._safe_filename(name) + ".json"
        filepath = self.data_dir / filename
        if filepath.exists():
            filepath.unlink()
            return f"Workflow '{name}' deleted."
        return f"Workflow '{name}' not found."


workflow_store = WorkflowStore()
