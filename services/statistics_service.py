"""Statistics service — computes per-document analytics."""
import re
from collections import Counter

# Common English stop words to exclude from keyword analysis
_STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "as", "was", "are", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "this",
    "that", "these", "those", "i", "you", "he", "she", "we", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "what", "which", "who", "whom", "when", "where", "why",
    "how", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "no", "not", "only", "own", "so", "than", "too",
    "very", "just", "about", "above", "after", "again", "also", "am",
    "any", "because", "before", "between", "below", "during", "if",
    "into", "through", "then", "there", "here", "up", "out", "off",
    "over", "under", "further", "once", "s", "t", "d", "re", "ve", "ll",
})

_WORD_PATTERN = re.compile(r"[a-zA-Z'\u00C0-\u024F]+")


class StatisticsService:
    """Compute text statistics for documents."""

    @staticmethod
    def compute(text: str) -> dict:
        """
        Compute all statistics for a text blob.

        Returns dict with keys:
            word_count, unique_words, char_count, line_count,
            reading_time_min, top_keywords
        """
        words = _WORD_PATTERN.findall(text.lower())
        word_count = len(words)
        unique_words = len(set(words))
        char_count = len(text)
        line_count = text.count("\n") + 1 if text else 0
        reading_time_min = round(word_count / 250, 1) if word_count > 0 else 0.0

        # Top 20 keywords (non-stop, >= 2 chars)
        meaningful = [w for w in words if w not in _STOP_WORDS and len(w) >= 2]
        top_keywords = Counter(meaningful).most_common(20)

        return {
            "word_count": word_count,
            "unique_words": unique_words,
            "char_count": char_count,
            "line_count": line_count,
            "reading_time_min": reading_time_min,
            "top_keywords": top_keywords,  # list of (word, count)
        }
