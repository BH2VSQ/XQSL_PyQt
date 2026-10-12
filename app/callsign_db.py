from __future__ import annotations

import re
from collections import Counter
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
        """Rank exact, substring, fragmented and approximate callsign matches."""
        raw_query = self._normalize(query)
        tokens = [token for token in re.findall(r"[A-Z0-9]+", raw_query) if token]
        q = "".join(tokens)
        callsigns = self._read()
        if not q:
            return callsigns[:limit]

        ranked: list[tuple[int, str]] = []
        for call in callsigns:
            candidate = self._search_normalize(call)
            if not candidate:
                continue

            score: int | None = None
            if candidate == q:
                score = 10000
            elif len(q) == 2 and candidate.endswith(q):
                # For two-character fragments, a suffix may be more informative
                # than hundreds of callsigns sharing the same prefix.
                score = 9200 - (len(candidate) - len(q))
            elif candidate.startswith(q):
                score = 9000 - len(candidate)
            elif candidate.endswith(q):
                # Suffixes are useful when only the end of a callsign was copied.
                score = 8500 - (len(candidate) - len(q))
            elif q in candidate:
                score = 8000 - candidate.find(q)
            elif len(tokens) > 1 and all(token in candidate for token in tokens):
                # Whitespace-separated pieces may be heard in any order, e.g. "SQ B".
                spans = [(candidate.find(token), candidate.find(token) + len(token)) for token in tokens]
                span = max(end for _, end in spans) - min(start for start, _ in spans)
                score = 7000 - span - sum(start for start, _ in spans)
            else:
                gap = self._subsequence_gap(q, candidate)
                if gap is not None:
                    score = 6000 - gap
                elif len(q) >= 3 and all(
                    candidate.count(char) >= needed
                    for char, needed in Counter(q).items()
                ):
                    # Also allow the received characters to arrive out of order.
                    score = 5000 - len(candidate)
                elif len(q) >= 4:
                    distance = self._substring_edit_distance(q, candidate)
                    if distance <= max(1, len(q) // 4):
                        score = 4000 - distance * 100

            if score is not None:
                ranked.append((score, call))

        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [call for _, call in ranked[:limit]]

    @staticmethod
    def _search_normalize(value: str) -> str:
        """Ignore spaces and punctuation for matching, preserving stored callsigns."""
        return "".join(char for char in value.upper() if char.isalnum())

    @staticmethod
    def _subsequence_gap(query: str, text: str) -> int | None:
        """Return the gap count when all query characters appear in order."""
        if not query:
            return 0
        positions: list[int] = []
        cursor = 0
        for char in query:
            position = text.find(char, cursor)
            if position < 0:
                return None
            positions.append(position)
            cursor = position + 1
        return positions[-1] - positions[0] + 1 - len(positions)

    @classmethod
    def _is_subsequence(cls, query: str, text: str) -> bool:
        """Backward-compatible subsequence predicate."""
        return cls._subsequence_gap(query, text) is not None

    @staticmethod
    def _substring_edit_distance(query: str, text: str) -> int:
        """Levenshtein distance from query to the best substring of text."""
        previous = [0] * (len(text) + 1)
        for row, char in enumerate(query, start=1):
            current = [row] + [0] * len(text)
            for column, candidate_char in enumerate(text, start=1):
                current[column] = min(
                    previous[column] + 1,
                    current[column - 1] + 1,
                    previous[column - 1] + (char != candidate_char),
                )
            previous = current
        return min(previous) if previous else len(query)

    def all_callsigns(self) -> list[str]:
        return self._read()
