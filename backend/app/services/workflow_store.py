import json
import os
import shutil
import difflib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from app.core.config import DATA_DIR


class WorkflowStore:
    def __init__(self, data_dir: str = str(DATA_DIR / "workflows"), versions_dir: str = str(DATA_DIR / "workflow_versions")):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir = Path(versions_dir)
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def _safe_filename(self, name: str) -> str:
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        return safe[:100]

    def _version_dir(self, name: str) -> Path:
        vdir = self.versions_dir / self._safe_filename(name)
        vdir.mkdir(parents=True, exist_ok=True)
        return vdir

    def save(self, name: str, workflow: Dict) -> str:
        filename = self._safe_filename(name) + ".json"
        filepath = self.data_dir / filename
        existing = None
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = None
        workflow["name"] = name
        workflow["saved_at"] = datetime.now().isoformat()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2, default=str)
        if existing:
            self._save_version(name, existing)
        return f"Workflow '{name}' saved successfully."

    def _save_version(self, name: str, workflow: Dict) -> Optional[str]:
        vdir = self._version_dir(name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_file = vdir / f"v_{timestamp}.json"
        workflow["_version_timestamp"] = timestamp
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2, default=str)
        versions = self.list_versions(name)
        if len(versions) > 20:
            oldest = versions[-1]
            oldest_path = vdir / oldest["filename"]
            if oldest_path.exists():
                oldest_path.unlink()
        return timestamp

    def list_versions(self, name: str) -> List[Dict]:
        vdir = self._version_dir(name)
        versions = []
        for vf in sorted(vdir.glob("v_*.json"), reverse=True):
            try:
                with open(vf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                versions.append({
                    "filename": vf.name,
                    "timestamp": data.get("_version_timestamp", vf.stem.replace("v_", "")),
                    "saved_at": data.get("saved_at", "Unknown"),
                    "node_count": len(data.get("nodes", []))
                })
            except Exception:
                pass
        return versions

    def load_version(self, name: str, timestamp: str) -> Optional[Dict]:
        vdir = self._version_dir(name)
        version_file = vdir / f"v_{timestamp}.json"
        if not version_file.exists():
            return None
        with open(version_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.pop("_version_timestamp", None)
        return data

    def rollback(self, name: str, timestamp: str) -> str:
        version_data = self.load_version(name, timestamp)
        if version_data is None:
            return f"Version '{timestamp}' not found for workflow '{name}'."
        version_data.pop("saved_at", None)
        filename = self._safe_filename(name) + ".json"
        filepath = self.data_dir / filename
        current = None
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    current = json.load(f)
            except Exception:
                current = None
        if current:
            self._save_version(name, current)
        version_data["name"] = name
        version_data["saved_at"] = datetime.now().isoformat()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=2, default=str)
        return f"Rolled back '{name}' to version '{timestamp}'."

    def diff_versions(self, name: str, ts1: str, ts2: str) -> str:
        v1 = self.load_version(name, ts1)
        v2 = self.load_version(name, ts2)
        if v1 is None or v2 is None:
            return "One or both versions not found."
        nodes1 = {n["id"]: n for n in v1.get("nodes", [])}
        nodes2 = {n["id"]: n for n in v2.get("nodes", [])}
        added = set(nodes2.keys()) - set(nodes1.keys())
        removed = set(nodes1.keys()) - set(nodes2.keys())
        modified = []
        for nid in set(nodes1.keys()) & set(nodes2.keys()):
            if json.dumps(nodes1[nid], sort_keys=True) != json.dumps(nodes2[nid], sort_keys=True):
                modified.append(nid)
        edges1 = v1.get("edges", [])
        edges2 = v2.get("edges", [])
        lines = [f"Diff between {ts1} and {ts2}:", ""]
        if added:
            lines.append(f"Added nodes: {', '.join(sorted(added))}")
        if removed:
            lines.append(f"Removed nodes: {', '.join(sorted(removed))}")
        if modified:
            lines.append(f"Modified nodes: {', '.join(sorted(modified))}")
        if not added and not removed and not modified:
            lines.append("No differences found.")
        return "\n".join(lines)

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
