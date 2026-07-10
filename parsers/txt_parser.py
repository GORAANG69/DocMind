"""Plain-text parser with encoding fallback."""
from pathlib import Path

from parsers.base_parser import BaseParser

_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1", "cp1252", "ascii")


class TxtParser(BaseParser):
    """Extract text from plain text files with multi-encoding fallback."""

    def extract_text(self, file_path: Path) -> str:
        for encoding in _ENCODINGS:
            try:
                text = file_path.read_text(encoding=encoding)
                if text.strip():
                    return text
                raise ValueError(f"File '{file_path.name}' is empty.")
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(
            f"Cannot decode '{file_path.name}' with any supported encoding."
        )

    @staticmethod
    def supported_extensions() -> list[str]:
        return [".txt", ".text", ".md", ".log", ".xml", ".html"]
