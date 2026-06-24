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
    snippet: str
    match_count: int
    positions: list[int] = field(default_factory=list)


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
        escaped = re.escape(query)
        if whole_word:
            escaped = rf"\b{escaped}\b"

        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(escaped, flags)

        # Fetch candidate rows (pre-filter with SQLite LIKE for speed)
        like_query = query if case_sensitive else query.lower()
        rows = self._db.search_content(like_query)

        results: list[SearchResult] = []
        for doc_id, filename, text in rows:
            matches = list(pattern.finditer(text))
            if not matches:
                continue

            # Build snippet around first match
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
                    snippet=snippet,
                    match_count=len(matches),
                    positions=[m.start() for m in matches],
                )
            )

        results.sort(key=lambda r: r.match_count, reverse=True)
        return results
