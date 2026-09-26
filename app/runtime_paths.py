from __future__ import annotations

import shutil
import sys
from pathlib import Path


def application_dir() -> Path:
    """Return the directory where the executable/source project lives."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def bundled_dir() -> Path:
    """Return PyInstaller's extracted resource directory when frozen."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return application_dir()


def prepare_data_directory() -> Path:
    """Ensure editable data files exist next to the application.

    In a PyInstaller one-file build, bundled files live in a temporary read-only
    extraction directory. Editable files therefore need to be copied to a
    persistent data/ directory next to the EXE on first launch.
    """
    app_dir = application_dir()
    target = app_dir / "data"
    target.mkdir(parents=True, exist_ok=True)

    bundled = bundled_dir() / "data"
    for filename in ("satellites.json", "callsigns.txt"):
        dst = target / filename
        src = bundled / filename
        if not dst.exists() and src.exists():
            try:
                shutil.copy2(src, dst)
            except OSError as exc:
                raise RuntimeError(f"无法释放数据文件到 {dst}: {exc}") from exc
    return target


def resource_path(*parts: str) -> Path:
    """Return a path to a bundled read-only resource."""
    return bundled_dir().joinpath("resources", *parts)
