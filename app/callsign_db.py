from __future__ import annotations

from pathlib import Path


class CallsignDatabase:
    """Simple line-based call sign database stored as data/callsigns.txt."""

    def __init__(self, root: Path):
        self.path = root / "data" / "callsigns.txt"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")
        self._sort_and_deduplicate()

    @staticmethod
    def _normalize(callsign: str) -> str:
        return callsign.strip().upper()

    def _read(self) -> list[str]:
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []

        callsigns: set[str] = set()
        for line in lines:
            call = self._normalize(line)
            if call:
                callsigns.add(call)
        return sorted(callsigns)

    def _write(self, callsigns: list[str]) -> None:
        try:
            self.path.write_text(
                "".join(f"{call}\n" for call in callsigns),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _sort_and_deduplicate(self) -> None:
        self._write(self._read())

    def record(self, callsign: str) -> bool:
        """Add a new call sign in alphabetical order. Returns True if inserted."""
        call = self._normalize(callsign)
        if not call:
            return False

        callsigns = self._read()
        if call in callsigns:
            return False

        callsigns.append(call)
        callsigns.sort()
        self._write(callsigns)
        return True

    def contains(self, callsign: str) -> bool:
        call = self._normalize(callsign)
        return bool(call) and call in set(self._read())

    def remove(self, callsign: str) -> bool:
        call = self._normalize(callsign)
        callsigns = self._read()
        if call not in callsigns:
            return False
        callsigns.remove(call)
        self._write(callsigns)
        return True

    def search(self, query: str, limit: int = 80) -> list[str]:
        # Drop whitespace so partial input like "B SQ" matches "BH2VSQ".
        q = "".join(self._normalize(query).split())
        callsigns = self._read()
        if not q:
            return callsigns[:limit]

        prefix: list[str] = []
        contains: list[str] = []
        subsequence: list[str] = []
        for call in callsigns:
            if call.startswith(q):
                prefix.append(call)
            elif q in call:
                contains.append(call)
            elif self._is_subsequence(q, call):
                subsequence.append(call)
        return (prefix + contains + subsequence)[:limit]

    @staticmethod
    def _is_subsequence(q: str, text: str) -> bool:
        """True when q's characters appear in ``text`` in order (not necessarily adjacent)."""
        pos = 0
        for ch in q:
            pos = text.find(ch, pos)
            if pos == -1:
                return False
            pos += 1
        return True

    def all_callsigns(self) -> list[str]:
        return self._read()
