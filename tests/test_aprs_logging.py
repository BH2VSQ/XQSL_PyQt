from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from app.qso_core import QSOEngine
from app.satellite_manager import SatelliteManager
from app.data_sync import _sync_satellites


class APRSLoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_dir = Path(__file__).resolve().parents[1] / "data"
        self.manager = SatelliteManager(self.data_dir / "satellites.json")
        self.engine = QSOEngine(self.manager)
        self.default_dt = datetime(2026, 11, 2, 12, 30, 0)

    def create_qso(self, satellite: str, frequency: float):
        return self.engine.generate_satellite_qso(
            satellite_name=satellite,
            row_callsign="JA1ABC",
            row_time="2026-11-02 12:30:00",
            default_dt=self.default_dt,
            mode_override="PKT",
            frequency_override_mhz=frequency,
        )

    def test_ariss_aprs_supports_all_simplex_frequencies(self) -> None:
        for frequency, band in (
            (145.825, "2M"),
            (437.825, "70CM"),
            (437.550, "70CM"),
        ):
            with self.subTest(frequency=frequency):
                qso = self.create_qso("ARISS-APRS", frequency)
                self.assertEqual(qso.mode, "PKT")
                self.assertEqual(qso.satelitename, "ARISS")
                self.assertEqual(qso.band, band)

                adif = self.engine.generate_adif_file([qso])
                freq = f"{frequency:.3f}"
                self.assertIn(f"<FREQ:{len(freq)}>{freq}", adif)
                self.assertIn(f"<FREQ_RX:{len(freq)}>{freq}", adif)
                self.assertIn("<MODE:3>PKT", adif)
                self.assertIn("<SAT_NAME:5>ARISS", adif)
                self.assertIn(f"<BAND_RX:{len(band)}>{band}", adif)

    def test_sonate_aprs_uses_sonate_adif_identity_and_145_825_mhz(self) -> None:
        qso = self.create_qso("SONATE-2-APRS", 145.825)
        self.assertEqual(qso.mode, "PKT")
        self.assertEqual(qso.satelitename, "SONATE")
        self.assertEqual(qso.band, "2M")

        adif = self.engine.generate_adif_file([qso])
        self.assertIn("<FREQ:7>145.825", adif)
        self.assertIn("<FREQ_RX:7>145.825", adif)
        self.assertIn("<SAT_NAME:6>SONATE", adif)

    def test_aprs_rejects_unsupported_frequency(self) -> None:
        with self.assertRaisesRegex(ValueError, "不支持频率"):
            self.create_qso("ARISS-APRS", 144.800)

    def test_existing_ariss_fm_profile_remains_unchanged(self) -> None:
        qso = self.engine.generate_satellite_qso(
            satellite_name="ARISS",
            row_callsign="JA1ABC",
            row_time="2026-11-02 12:30:00",
            default_dt=self.default_dt,
        )
        self.assertEqual(qso.satelitename, "ARISS")
        self.assertEqual(qso.mode, "FM")
        self.assertEqual(qso.freq, "145.99↑ 437.8↓")

    def test_bundled_upgrade_adds_aprs_profiles_and_preserves_local_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            local_path = Path(temporary_dir) / "satellites.json"
            old_config = json.loads((self.data_dir / "satellites.json").read_text(encoding="utf-8"))
            old_config["version"] = 1
            old_config["satellites"] = [
                item for item in old_config["satellites"]
                if item["name"] not in {"ARISS-APRS", "SONATE-2-APRS"}
            ]
            old_config["satellites"].append({
                "name": "MY-CUSTOM-SAT",
                "uplink_mhz": 145.900,
                "downlink_mhz": 435.900,
            })
            local_path.write_text(json.dumps(old_config), encoding="utf-8")

            added = _sync_satellites(self.data_dir / "satellites.json", local_path)
            updated = json.loads(local_path.read_text(encoding="utf-8"))
            names = {item["name"] for item in updated["satellites"]}

            self.assertEqual(added, 2)
            self.assertEqual(updated["version"], 2)
            self.assertIn("ARISS-APRS", names)
            self.assertIn("SONATE-2-APRS", names)
            self.assertIn("MY-CUSTOM-SAT", names)


if __name__ == "__main__":
    unittest.main()
