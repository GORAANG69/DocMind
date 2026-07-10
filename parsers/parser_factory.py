"""Parser factory — maps file extensions to the correct parser."""
from pathlib import Path

from parsers.base_parser import BaseParser
from parsers.pdf_parser import PdfParser
from parsers.docx_parser import DocxParser
from parsers.xlsx_parser import XlsxParser
from parsers.xls_parser import XlsParser
from parsers.txt_parser import TxtParser
from parsers.csv_parser import CsvParser
from parsers.json_parser import JsonParser

_PARSER_MAP: dict[str, type[BaseParser]] = {}


def _register_parsers():
    """Build the extension → parser lookup once."""
    for cls in (PdfParser, DocxParser, XlsxParser, XlsParser, TxtParser, CsvParser, JsonParser):
        for ext in cls.supported_extensions():
            _PARSER_MAP[ext.lower()] = cls


_register_parsers()

SUPPORTED_EXTENSIONS = sorted(_PARSER_MAP.keys())


class ParserFactory:
    """Return the appropriate parser for a file's extension."""

    @staticmethod
    def get_parser(file_path: Path) -> BaseParser:
        ext = file_path.suffix.lower()
        parser_cls = _PARSER_MAP.get(ext)
        if parser_cls is None:
            raise ValueError(
                f"Unsupported file type '{ext}'. "
                f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        return parser_cls()

    @staticmethod
    def is_supported(file_path: Path) -> bool:
        return file_path.suffix.lower() in _PARSER_MAP
