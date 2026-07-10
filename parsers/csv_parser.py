"""CSV parser for extracting cell-level text."""
import csv
from pathlib import Path

from parsers.base_parser import BaseParser


class CsvParser(BaseParser):
    """Extract text from CSV files cell-by-cell."""

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
            raise ValueError(f"Cannot decode CSV '{file_path.name}' with any supported encoding.")

        # Detect delimiter using simple heuristics
        lines = [line for line in text_content.splitlines() if line.strip()]
        if not lines:
            raise ValueError(f"CSV '{file_path.name}' is empty.")

        delimiter = ","
        try:
            dialect = csv.Sniffer().sniff(lines[0])
            delimiter = dialect.delimiter
        except Exception:
            # Fallback delimiters
            for delim in (",", ";", "\t", "|"):
                if delim in lines[0]:
                    delimiter = delim
                    break

        parts: list[str] = []
        try:
            reader = csv.reader(text_content.splitlines(), delimiter=delimiter)
            for row_idx, row in enumerate(reader):
                for col_idx, val in enumerate(row):
                    val_str = str(val).strip()
                    if val_str:
                        col_letter = self._get_column_letter(col_idx)
                        coordinate = f"{col_letter}{row_idx + 1}"
                        parts.append(f"CSV\t{coordinate}\t{val_str}")
        except Exception as exc:
            raise ValueError(f"Cannot parse CSV '{file_path.name}': {exc}") from exc

        if not parts:
            raise ValueError(f"CSV '{file_path.name}' contains no extractable data.")

        return "\n".join(parts)

    @staticmethod
    def _get_column_letter(col_idx: int) -> str:
        """Convert 0-indexed column column index to spreadsheet column letter (A, B, C...)."""
        result = ""
        col_idx += 1
        while col_idx > 0:
            col_idx, remainder = divmod(col_idx - 1, 26)
            result = chr(65 + remainder) + result
        return result

    @staticmethod
    def supported_extensions() -> list[str]:
        return [".csv"]
