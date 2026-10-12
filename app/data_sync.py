from __future__ import annotations

import json
from pathlib import Path

from .runtime_paths import bundled_dir


def sync_bundled_data(root: Path) -> dict[str, int]:
    """Merge newer bundled satellite/callsign data into the writable data dir.

    User-added satellites and callsigns are preserved. Bundled files are read
    from PyInstaller's resource directory; when running from source, both paths
    resolve to the same directory and no sync is needed.
    """
    local_dir = root / "data"
    bundled_data_dir = bundled_dir() / "data"
    if _same_path(local_dir, bundled_data_dir):
        return {"satellites_added": 0, "callsigns_added": 0}

    return {
        "satellites_added": _sync_satellites(
            bundled_data_dir / "satellites.json",
            local_dir / "satellites.json",
        ),
        "callsigns_added": _sync_callsigns(
            bundled_data_dir / "callsigns.txt",
            local_dir / "callsigns.txt",
        ),
    }


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return False


def _write_json_atomic(path: Path, payload: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sync_satellites(source: Path, target: Path) -> int:
    """When the bundled schema version is newer, append missing satellites."""
    try:
        bundled = json.loads(source.read_text(encoding="utf-8"))
        local = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(bundled, dict) or not isinstance(local, dict):
            return 0
        bundled_version = int(bundled.get("version", 0))
        local_version = int(local.get("version", 0))
        bundled_satellites = bundled.get("satellites", [])
        local_satellites = local.get("satellites", [])
        if not isinstance(bundled_satellites, list) or not isinstance(local_satellites, list):
            return 0
        if bundled_version <= local_version:
            return 0

        merged = list(local_satellites)
        existing_names = {
            str(item.get("name", "")).strip().casefold()
            for item in merged
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        }
        added = 0
        for item in bundled_satellites:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            key = name.casefold()
            if name and key not in existing_names:
                merged.append(item)
                existing_names.add(key)
                added += 1

        updated = dict(local)
        updated["version"] = bundled_version
        updated["satellites"] = merged
        _write_json_atomic(target, updated)
        return added
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        # A malformed or inaccessible data file must never prevent startup.
        return 0


def _sync_callsigns(source: Path, target: Path) -> int:
    """Add missing bundled callsigns if local data is empty or overlaps it."""
    try:
        bundled_lines = source.read_text(encoding="utf-8").splitlines()
        local_lines = target.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0

    bundled = {line.strip().upper() for line in bundled_lines if line.strip()}
    local = {line.strip().upper() for line in local_lines if line.strip()}
    missing = bundled - local
    if not missing:
        return 0

    # Empty files can be repaired from the bundled base. For non-empty custom
    # lists, require some overlap to avoid merging an unrelated callsign set.
    if local and not (local & bundled):
        return 0

    merged = sorted(local | bundled)
    temporary = target.with_name(target.name + ".tmp")
    try:
        temporary.write_text("".join(f"{call}\n" for call in merged), encoding="utf-8")
        temporary.replace(target)
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return 0
    return len(missing)
