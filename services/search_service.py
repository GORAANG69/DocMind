"""Search service — full-text search across documents."""
import re
from dataclasses import dataclass, field
from typing import Optional

from database.db_manager import DatabaseManager


@dataclass
class SearchResult:
    """A single search match."""

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
    ) -> list[SearchResult]:
        """
        Search all documents for the query string.

        Args:
            query: The search term or phrase.
            case_sensitive: Whether matching is case-sensitive.
            whole_word: Whether to match whole words only.
            exact_phrase: If True, treat query as an exact phrase.

        Returns:
            List of SearchResult sorted by match_count descending.
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

        results: list[SearchResult] = []
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
                        
                    results.append(
                        SearchResult(
                            doc_id=doc_id,
                            filename=filename,
                            file_type=file_type,
                            snippet=snippet,
                            match_count=len(matches),
                            page_number=page_idx,
                            positions=[m.start() for m in matches],
                            original_filename=filename,
                        )
                    )
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
                            
                        results.append(
                            SearchResult(
                                doc_id=doc_id,
                                filename=filename,
                                file_type=file_type,
                                snippet=snippet,
                                match_count=len(matches),
                                sheet_name=sheet_name,
                                cell_ref=cell_ref,
                                positions=[m.start() for m in matches],
                                original_filename=filename,
                            )
                        )
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
                    
                results.append(
                    SearchResult(
                        doc_id=doc_id,
                        filename=filename,
                        file_type=file_type,
                        snippet=snippet,
                        match_count=len(matches),
                        positions=[m.start() for m in matches],
                        original_filename=filename,
                    )
                )

        results.sort(key=lambda r: r.match_count, reverse=True)
        return results
