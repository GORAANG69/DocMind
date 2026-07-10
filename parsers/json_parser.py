"""JSON parser for extracting structured nested keys and values."""
import json
from pathlib import Path

from parsers.base_parser import BaseParser


class JsonParser(BaseParser):
    """Extract text recursively from JSON objects, arrays, keys, and values."""

    def extract_text(self, file_path: Path) -> str:
        # Try different encodings
        encodings = ("utf-8", "utf-8-sig", "latin-1", "cp1252", "ascii")
        text_content = ""
        for encoding in encodings:
            try:
                text_content = file_path.read_text(encoding=encoding)
                break
            except Exception:
                continue

        if not text_content:
            raise ValueError(f"Cannot decode JSON '{file_path.name}' with any supported encoding.")

        try:
            data = json.loads(text_content)
        except Exception as exc:
            # Malformed JSON: try to fall back to plain text content if readable
            if text_content.strip():
                return text_content.strip()
            raise ValueError(f"Malformed JSON in '{file_path.name}': {exc}") from exc

        # Format recursively as pretty printed JSON with indent of 2 spaces
        try:
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as exc:
            raise ValueError(f"Cannot format JSON '{file_path.name}': {exc}") from exc

    @staticmethod
    def supported_extensions() -> list[str]:
        return [".json"]
