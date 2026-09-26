from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from .satellite_manager import SatelliteManager


@dataclass
class QSOData:
    freq: str
    qsotime: str
    satelitename: str
    qso_callsigns: list[str]
    mode: str
    band: str


CALLSIGN_RE = re.compile(
    r"^([A-Z0-9]{1,3}/)?([A-Z0-9]{1,2}[0-9]{1,2}[A-Z0-9]{0,3}[A-Z])(/[A-Z0-9]{1,3})?$",
    re.I,
)


def parse_log_time(value: str, default_dt: datetime) -> datetime:
    text = value.strip()
    if not text:
        return default_dt.replace(microsecond=0)

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y%m%d %H%M%S",
        "%Y%m%d%H%M%S",
        "%H%M",
        "%H:%M",
        "%H:%M:%S",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            if fmt in {"%H%M", "%H:%M", "%H:%M:%S"}:
                return default_dt.replace(
                    hour=parsed.hour,
                    minute=parsed.minute,
                    second=parsed.second,
                    microsecond=0,
                )
            return parsed.replace(microsecond=0)
        except ValueError:
            continue

    raise ValueError(f"无法识别时间：{value}")


class QSOEngine:
    def __init__(self, satellite_manager: SatelliteManager):
        self.satellite_manager = satellite_manager

    def generate_satellite_qso(
        self,
        satellite_name: str,
        row_callsign: str,
        row_time: str,
        default_dt: datetime,
        mode_override: str | None = None,
    ) -> QSOData:
        sat = self.satellite_manager.get(satellite_name)
        if sat is None:
            raise ValueError(f"未找到卫星：{satellite_name}")

        call = row_callsign.strip().upper()
        if not CALLSIGN_RE.fullmatch(call):
            raise ValueError(f"呼号格式无效：{call}")

        dt = parse_log_time(row_time, default_dt)
        qso_time = dt.strftime("%Y%m%d %H%M%S")
        mode = (mode_override or sat.modes[0]).strip().upper()
        if mode not in sat.modes:
            raise ValueError(
                f"卫星 {sat.name} 不支持模式 {mode}，可选：{', '.join(sat.modes)}"
            )

        tx_band = "70CM" if 420 <= sat.uplink_mhz <= 450 else "2M"
        return QSOData(
            freq=sat.frequency_text,
            qsotime=qso_time,
            satelitename=sat.name,
            qso_callsigns=[call],
            mode=mode,
            band=tx_band,
        )

    @staticmethod
    def generate_adif_file(qso_list: list[QSOData]) -> str:
        lines = [
            "<ADIF_VERS:3>2.2",
            f"<CREATED_TIMESTAMP:15>{datetime.utcnow().strftime('%Y%m%d %H%M%S')}",
            "<PROGRAMID:7>SAT_QSO",
            "<PROGRAMVERSION:5>2.4.4",
            "<EOH>",
            "",
        ]

        for qso in qso_list:
            if not qso.qsotime or not qso.qso_callsigns or not qso.mode or not qso.band:
                continue

            date_part, time_part = qso.qsotime.split(" ", 1)
            numbers = re.findall(r"\d+(?:\.\d+)?", qso.freq)
            if len(numbers) < 2:
                continue

            tx_mhz = float(numbers[0])
            rx_mhz = float(numbers[1])
            rx_band = "70CM" if 420 <= rx_mhz <= 450 else "2M"
            tx_freq = f"{tx_mhz:g}"
            rx_freq = f"{rx_mhz:g}"

            for call in qso.qso_callsigns:
                if not call:
                    continue
                lines.extend([
                    f"<CALL:{len(call)}>{call}",
                    f"<BAND:{len(qso.band)}>{qso.band}",
                    f"<MODE:{len(qso.mode)}>{qso.mode}",
                    f"<QSO_DATE:{len(date_part)}>{date_part}",
                    f"<TIME_ON:{len(time_part)}>{time_part}",
                    f"<FREQ:{len(tx_freq)}>{tx_freq}",
                    f"<BAND_RX:{len(rx_band)}>{rx_band}",
                    f"<FREQ_RX:{len(rx_freq)}>{rx_freq}",
                    "<PROP_MODE:3>SAT",
                    f"<SAT_NAME:{len(qso.satelitename)}>{qso.satelitename}",
                    "<EOR>",
                ])

        return "\n".join(lines) + "\n"
