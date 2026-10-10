"""GitHub release updater for the PyInstaller one-file build.

Kept free of Qt so it can be reused and tested without a GUI. Only the
standard library is used, so the frozen application needs no extra
dependencies.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from .runtime_paths import resource_path

REPO = "BH2VSQ/XQSL_PyQt"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
USER_AGENT = "XQSL-PyQt-Updater"

_download_path: Path | None = None


def current_version() -> str:
    """Return the version bundled with this build (e.g. ``V1.2``)."""
    try:
        return resource_path("version.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return "V0.0"


def parse_version(version: str) -> tuple[int, ...]:
    """Convert ``V1.2`` / ``v1.2.3`` into a comparable tuple of ints."""
    return tuple(int(part) for part in re.findall(r"\d+", version))


def can_self_update() -> bool:
    """Only a frozen one-file exe can safely replace itself while running."""
    return bool(getattr(sys, "frozen", False))


def _exe_dir() -> Path:
    if can_self_update():
        return Path(sys.executable).resolve().parent
    return Path(tempfile.gettempdir())


def check_for_update() -> dict:
    """Query the latest GitHub release and compare it against the local build."""
    current = current_version()
    request = urllib.request.Request(
        LATEST_RELEASE_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    latest = str(data.get("tag_name", ""))
    assets = data.get("assets", [])
    download_url = ""
    for asset in assets:
        name = str(asset.get("name", "")).lower()
        if name.endswith(".exe"):
            download_url = str(asset.get("browser_download_url", ""))
            break
    if not download_url and assets:
        download_url = str(assets[0].get("browser_download_url", ""))

    return {
        "current": current,
        "latest": latest,
        "update_available": bool(latest) and parse_version(latest) > parse_version(current),
        "download_url": download_url,
        "html_url": str(data.get("html_url", "")),
        "can_self_update": can_self_update(),
    }


def download_and_prepare(url: str) -> bool:
    """Download the new exe next to the running one and stage it for replacement."""
    global _download_path
    dest = _exe_dir() / "XQSL_PyQt.new.exe"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response, open(dest, "wb") as fh:
        shutil.copyfileobj(response, fh)
    _download_path = dest
    return True


def apply_downloaded() -> None:
    """Replace the running exe via a detached helper script, then relaunch."""
    global _download_path
    if not _download_path or not _download_path.exists() or not can_self_update():
        return

    exe = Path(sys.executable).resolve()
    bat = _exe_dir() / "update.bat"
    bat.write_text(UPDATE_BAT, encoding="ascii")

    subprocess.Popen(
        ["cmd", "/c", str(bat), str(exe), str(_download_path)],
        creationflags=(
            getattr(subprocess, "CREATE_NO_WINDOW", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
        ),
        close_fds=True,
    )


UPDATE_BAT = """\
@echo off
setlocal enabledelayedexpansion
set "app=%~1"
set "new=%~2"
set "tries=0"
:retry
timeout /t 1 /nobreak >nul
move /Y "%new%" "%app%" >nul 2>&1
if exist "%new%" (
    set /a tries+=1
    if !tries! lss 15 goto retry
)
if exist "%app%" start "" "%app%"
del "%~f0" >nul 2>&1
"""
