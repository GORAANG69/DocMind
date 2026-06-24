"""PDF parser using PyMuPDF (fitz)."""
from pathlib import Path

import fitz  # PyMuPDF

from parsers.base_parser import BaseParser


class PdfParser(BaseParser):
    """Extract text from PDF files using PyMuPDF."""

    def extract_text(self, file_path: Path) -> str:
        try:
            doc = fitz.open(str(file_path))
        except Exception as exc:
            raise ValueError(f"Cannot open PDF '{file_path.name}': {exc}") from exc

        pages: list[str] = []
        for page_num in range(len(doc)):
            try:
                page = doc.load_page(page_num)
                text = page.get_text("text")
                if text.strip():
                    pages.append(text)
            except Exception:
                # Skip unreadable pages rather than failing entirely
                pages.append(f"[Page {page_num + 1}: could not extract text]")

        doc.close()

        if not pages:
            raise ValueError(f"PDF '{file_path.name}' contains no extractable text.")

        return "\n\n".join(pages)

    @staticmethod
    def supported_extensions() -> list[str]:
        return [".pdf"]
