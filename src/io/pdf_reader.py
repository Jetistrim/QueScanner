from __future__ import annotations

from pathlib import Path
from typing import Any

import pdfplumber  # type: ignore[reportMissingImports]


def extract_lines_from_pdf(pdf_path: Path) -> list[str]:
    lines: list[str] = []
    pdfplumber_module: Any = pdfplumber
    with pdfplumber_module.open(pdf_path) as pdf:
        for page in getattr(pdf, "pages", []):
            extractor = getattr(page, "extract_text", None)
            text_value = extractor(layout=False) if callable(extractor) else ""
            text = text_value if isinstance(text_value, str) else ""
            for line in text.splitlines():
                cleaned = line.strip()
                if cleaned:
                    lines.append(cleaned)
    return lines
