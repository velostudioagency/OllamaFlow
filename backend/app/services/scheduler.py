import json
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.config import DATA_DIR


class SchedulerManager:
    def __init__(self, data_dir: str = str(DATA_DIR)):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.schedules_file = self.data_dir / "schedules.json"
        self.schedules: Dict[str, Dict] = {}
        self.timers: Dict[str, threading.Timer] = {}
        self._load_schedules()
        self._restore_timers()

    def _load_schedules(self):
        if self.schedules_file.exists():
            try:
                with open(self.schedules_file, "r", encoding="utf-8") as f:
                    self.schedules = json.load(f)
            except Exception:
                self.schedules = {}

    def _save_schedules(self):
        with open(self.schedules_file, "w", encoding="utf-8") as f:
            json.dump(self.schedules, f, indent=2, default=str)

    def _restore_timers(self):
        for schedule_id, schedule in self.schedules.items():
            if schedule.get("enabled") and schedule.get("schedule_type") == "interval":
                interval = schedule.get("interval_minutes", 60) * 60
                timer = threading.Timer(interval, self._run_workflow, args=[schedule_id])
                timer.daemon = True
                timer.start()
                self.timers[schedule_id] = timer
                print(f"[Scheduler] Restored timer for '{schedule.get('name', schedule_id)}' (every {schedule.get('interval_minutes', 60)}min)")

    def _run_workflow(self, schedule_id: str):
        schedule = self.schedules.get(schedule_id)
        if not schedule or not schedule.get("enabled"):
            return

        workflow = schedule.get("workflow", {})
        print(f"[Scheduler] Running workflow: {schedule.get('name', schedule_id)}")

        schedule["last_run"] = datetime.now().isoformat()

        try:
            import requests
            resp = requests.post(
                "http://localhost:8000/api/run",
                json={"workflow": workflow},
                timeout=300
            )
            if resp.status_code == 200:
                print(f"[Scheduler] Workflow completed: {schedule.get('name', schedule_id)}")
            else:
                print(f"[Scheduler] Workflow failed: {resp.text}")
        except Exception as e:
            print(f"[Scheduler] Error running workflow: {e}")

        if schedule.get("enabled") and schedule.get("schedule_type") == "interval":
            interval = schedule.get("interval_minutes", 60) * 60
            schedule["next_run"] = (datetime.now() + timedelta(minutes=schedule.get("interval_minutes", 60))).isoformat()
            self.timers[schedule_id] = threading.Timer(interval, self._run_workflow, args=[schedule_id])
            self.timers[schedule_id].daemon = True
            self.timers[schedule_id].start()

        self._save_schedules()

    def add_schedule(self, schedule_id: str, workflow: Dict, name: str,
                     schedule_type: str = "interval", interval_minutes: int = 60,
                     cron_expression: str = "", enabled: bool = True) -> str:
        next_run = datetime.now() + timedelta(minutes=interval_minutes) if schedule_type == "interval" else None

        self.schedules[schedule_id] = {
            "id": schedule_id,
            "name": name,
            "workflow": workflow,
            "schedule_type": schedule_type,
            "interval_minutes": interval_minutes,
            "cron_expression": cron_expression,
            "enabled": enabled,
            "created_at": datetime.now().isoformat(),
            "next_run": next_run.isoformat() if next_run else None,
            "last_run": None
        }
        self._save_schedules()

        if enabled and schedule_type == "interval":
            interval = interval_minutes * 60
            self.timers[schedule_id] = threading.Timer(interval, self._run_workflow, args=[schedule_id])
            self.timers[schedule_id].daemon = True
            self.timers[schedule_id].start()

        return f"Schedule '{name}' created."

    def remove_schedule(self, schedule_id: str) -> str:
        if schedule_id in self.timers:
            self.timers[schedule_id].cancel()
            del self.timers[schedule_id]

        if schedule_id in self.schedules:
            name = self.schedules[schedule_id].get("name", schedule_id)
            del self.schedules[schedule_id]
            self._save_schedules()
            return f"Schedule '{name}' removed."
        return f"Schedule '{schedule_id}' not found."

    def toggle_schedule(self, schedule_id: str) -> str:
        if schedule_id not in self.schedules:
            return f"Schedule '{schedule_id}' not found."

        schedule = self.schedules[schedule_id]
        schedule["enabled"] = not schedule.get("enabled", True)

        if schedule["enabled"] and schedule.get("schedule_type") == "interval":
            interval = schedule.get("interval_minutes", 60) * 60
            self.timers[schedule_id] = threading.Timer(interval, self._run_workflow, args=[schedule_id])
            self.timers[schedule_id].daemon = True
            self.timers[schedule_id].start()
            status = "enabled"
        elif schedule_id in self.timers:
            self.timers[schedule_id].cancel()
            del self.timers[schedule_id]
            status = "disabled"

        self._save_schedules()
        return f"Schedule '{schedule.get('name', schedule_id)}' {status}."

    def list_schedules(self) -> List[Dict]:
        result = []
        for sid, s in self.schedules.items():
            result.append({
                "id": sid,
                "name": s.get("name", ""),
                "schedule_type": s.get("schedule_type", "interval"),
                "interval_minutes": s.get("interval_minutes", 60),
                "cron_expression": s.get("cron_expression", ""),
                "enabled": s.get("enabled", True),
                "created_at": s.get("created_at", ""),
                "next_run": s.get("next_run"),
                "last_run": s.get("last_run")
            })
        return result


scheduler_manager = SchedulerManager()
