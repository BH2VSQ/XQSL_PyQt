from __future__ import annotations

import json
from pathlib import Path


class StationConfig:
    def __init__(self, root: Path):
        self.path = root / "data" / "station.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.save("", "")

        self.load()


    def load(self):
        try:
            data = json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except Exception:
            data = {}

        self.callsign = str(
            data.get("callsign", "")
        ).upper()

        self.grid = str(
            data.get("grid", "")
        ).upper()


    def save(self, callsign: str, grid: str):

        data = {
            "callsign": callsign.strip().upper(),
            "grid": grid.strip().upper()
        }

        self.path.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        self.callsign = data["callsign"]
        self.grid = data["grid"]