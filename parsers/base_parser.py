"""Abstract base class for document parsers."""
from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    """Every parser must implement extract_text."""

    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """
        Extract plain text from the given file.

        Args:
            file_path: Path to the file on disk.

        Returns:
            Extracted text as a single string.

        Raises:
            ValueError: If the file cannot be parsed.
        """
        ...

    @staticmethod
    def supported_extensions() -> list[str]:
        """Return the list of file extensions this parser handles."""
        return []
