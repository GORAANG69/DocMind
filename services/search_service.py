"""Search service — full-text search across documents."""
import re
from dataclasses import dataclass, field
from typing import Optional

from database.db_manager import DatabaseManager


@dataclass
class SearchResult:
    """A single search match (legacy, kept for backward compatibility)."""

    doc_id: str
    filename: str
    file_type: str
    snippet: str
    match_count: int
    page_number: Optional[int] = None
    sheet_name: Optional[str] = None
    cell_ref: Optional[str] = None
    positions: list[int] = field(default_factory=list)
    original_filename: str = ""


@dataclass
class PageMatch:
    """A single page-level match within a document."""

    page_number: int
    match_count: int
    snippet: str
    positions: list[int] = field(default_factory=list)


@dataclass
class SheetMatch:
    """A single sheet/cell-level match within a spreadsheet document."""

    sheet_name: str
    cell_ref: str
    match_count: int
    snippet: str
    positions: list[int] = field(default_factory=list)


@dataclass
class GroupedSearchResult:
    """Search results grouped by document.

    One instance per document, containing all page/sheet-level hits.
    """

    doc_id: str
    filename: str
    file_type: str
    original_filename: str
    total_matches: int = 0
    pages: list[PageMatch] = field(default_factory=list)
    sheets: list[SheetMatch] = field(default_factory=list)
    # For non-paged documents (txt, docx, json), store a single snippet
    snippet: str = ""


class SearchService:
    """Search across all document texts."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()

    def search(
        self,
        query: str,
        *,
        case_sensitive: bool = False,
        whole_word: bool = False,
        exact_phrase: bool = True,
    ) -> list[GroupedSearchResult]:
        """
        Search all documents for the query string.

        Results are grouped by document — each document appears at most once.
        For PDFs, individual page hits are nested under ``pages``.
        For spreadsheets, individual cell hits are nested under ``sheets``.
        For text/docx/other, a single snippet is stored at the top level.

        Args:
            query: The search term or phrase.
            case_sensitive: Whether matching is case-sensitive.
            whole_word: Whether to match whole words only.
            exact_phrase: If True, treat query as an exact phrase.

        Returns:
            List of GroupedSearchResult sorted by total_matches descending.
        """
        if not query.strip():
            return []

        # Build regex pattern
        if exact_phrase:
            escaped = re.escape(query)
            if whole_word:
                escaped = rf"\b{escaped}\b"
            pattern_str = escaped
        else:
            # Keyword mode: match any of the words in the query
            words = [re.escape(w) for w in query.split() if w.strip()]
            if not words:
                return []
            if whole_word:
                words = [rf"\b{w}\b" for w in words]
            pattern_str = "|".join(words)

        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(pattern_str, flags)

        # Pre-filter with SQLite LIKE using a simpler search pattern
        first_word = query.split()[0] if not exact_phrase and query.strip() else query
        like_query = first_word if case_sensitive else first_word.lower()
        rows = self._db.search_content(like_query)

        # Collect results grouped by doc_id
        grouped: dict[str, GroupedSearchResult] = {}

        for doc_id, filename, file_type, text in rows:
            if file_type == ".pdf":
                # PDF: split by Form Feed page boundaries
                pages = text.split("\f")
                for page_idx, page_text in enumerate(pages, 1):
                    matches = list(pattern.finditer(page_text))
                    if not matches:
                        continue
                    first = matches[0]
                    start = max(0, first.start() - 60)
                    end = min(len(page_text), first.end() + 60)
                    snippet = page_text[start:end].replace("\n", " ").strip()
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(page_text):
                        snippet = snippet + "..."

                    page_match = PageMatch(
                        page_number=page_idx,
                        match_count=len(matches),
                        snippet=snippet,
                        positions=[m.start() for m in matches],
                    )

                    if doc_id not in grouped:
                        grouped[doc_id] = GroupedSearchResult(
                            doc_id=doc_id,
                            filename=filename,
                            file_type=file_type,
                            original_filename=filename,
                        )
                    grouped[doc_id].pages.append(page_match)
                    grouped[doc_id].total_matches += len(matches)

            elif file_type in (".xlsx", ".xls", ".csv"):
                # Excel/CSV: split by lines, each line is sheet\tcell\tvalue
                lines = text.split("\n")
                for line in lines:
                    if not line.strip():
                        continue
                    parts = line.split("\t", 2)
                    if len(parts) == 3:
                        sheet_name, cell_ref, cell_value = parts
                        matches = list(pattern.finditer(cell_value))
                        if not matches:
                            continue
                        first = matches[0]
                        start = max(0, first.start() - 60)
                        end = min(len(cell_value), first.end() + 60)
                        snippet = cell_value[start:end].strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(cell_value):
                            snippet = snippet + "..."

                        sheet_match = SheetMatch(
                            sheet_name=sheet_name,
                            cell_ref=cell_ref,
                            match_count=len(matches),
                            snippet=snippet,
                            positions=[m.start() for m in matches],
                        )

                        if doc_id not in grouped:
                            grouped[doc_id] = GroupedSearchResult(
                                doc_id=doc_id,
                                filename=filename,
                                file_type=file_type,
                                original_filename=filename,
                            )
                        grouped[doc_id].sheets.append(sheet_match)
                        grouped[doc_id].total_matches += len(matches)

            else:
                # Text / DOCX / other: search entire text
                matches = list(pattern.finditer(text))
                if not matches:
                    continue
                first = matches[0]
                start = max(0, first.start() - 60)
                end = min(len(text), first.end() + 60)
                snippet = text[start:end].replace("\n", " ").strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."

                if doc_id not in grouped:
                    grouped[doc_id] = GroupedSearchResult(
                        doc_id=doc_id,
                        filename=filename,
                        file_type=file_type,
                        original_filename=filename,
                    )
                grouped[doc_id].snippet = snippet
                grouped[doc_id].total_matches += len(matches)

        # Sort by total_matches descending
        results = sorted(grouped.values(), key=lambda r: r.total_matches, reverse=True)
        return results
