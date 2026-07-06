"""XLS parser using xlrd."""
from pathlib import Path
import xlrd
from parsers.base_parser import BaseParser


class XlsParser(BaseParser):
    """Extract text from Excel XLS files."""

    def extract_text(self, file_path: Path) -> str:
        try:
            wb = xlrd.open_workbook(str(file_path))
        except Exception as exc:
            raise ValueError(f"Cannot open XLS '{file_path.name}': {exc}") from exc

        parts: list[str] = []

        for sheet in wb.sheets():
            sheet_name = sheet.name
            for row_idx in range(sheet.nrows):
                for col_idx in range(sheet.ncols):
                    val = sheet.cell_value(row_idx, col_idx)
                    if val is not None and str(val).strip() != "":
                        col_letter = self._get_column_letter(col_idx)
                        cell_ref = f"{col_letter}{row_idx + 1}"
                        parts.append(f"{sheet_name}\t{cell_ref}\t{str(val).strip()}")

        if not parts:
            raise ValueError(f"XLS '{file_path.name}' contains no extractable data.")

        return "\n".join(parts)

    @staticmethod
    def _get_column_letter(col_idx: int) -> str:
        """Convert a 0-indexed column index to an Excel column letter (e.g. 0 -> A, 27 -> AB)."""
        result = ""
        col_idx += 1
        while col_idx > 0:
            col_idx, remainder = divmod(col_idx - 1, 26)
            result = chr(65 + remainder) + result
        return result

    @staticmethod
    def supported_extensions() -> list[str]:
        return [".xls"]
