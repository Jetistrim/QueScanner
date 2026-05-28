from __future__ import annotations

from pathlib import Path


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture_lines(name: str) -> list[str]:
    content = (FIXTURES_DIR / name).read_text(encoding="utf-8")
    return [line.rstrip("\n") for line in content.splitlines()]
