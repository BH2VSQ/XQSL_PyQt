from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Satellite:
    name: str
    aliases: tuple[str, ...]
    uplink_mhz: float
    downlink_mhz: float
    modes: tuple[str, ...] = ("FM",)

    @property
    def frequency_text(self) -> str:
        return f"{self.uplink_mhz:g}↑ {self.downlink_mhz:g}↓"


class SatelliteManager:
    def __init__(self, path: Path):
        self.path = path
        self.satellites: list[Satellite] = []
        self.load()

    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"无法读取卫星数据文件：{self.path}\n{exc}") from exc

        loaded: list[Satellite] = []
        for item in raw.get("satellites", []):
            raw_modes = item.get("modes", ["FM"])
            modes = tuple(dict.fromkeys(
                str(mode).strip().upper()
                for mode in raw_modes
                if str(mode).strip()
            )) or ("FM",)

            loaded.append(
                Satellite(
                    name=str(item["name"]).strip(),
                    aliases=tuple(
                        str(alias).strip()
                        for alias in item.get("aliases", [])
                        if str(alias).strip()
                    ),
                    uplink_mhz=float(item["uplink_mhz"]),
                    downlink_mhz=float(item["downlink_mhz"]),
                    modes=modes,
                )
            )

        self.satellites = loaded

    def get(self, name: str) -> Satellite | None:
        key = name.strip().upper()
        return next(
            (sat for sat in self.satellites if sat.name.upper() == key),
            None,
        )
