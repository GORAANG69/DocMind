"""Document viewer — displays extracted text with in-document search."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.models import Document
from services.document_service import DocumentService


class DocumentViewer(QWidget):
    """Read-only document viewer with in-text search and highlight."""

    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = DocumentService()
        self._current_doc: Document | None = None
        self._match_positions: list = []
        self._current_match: int = -1
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # ── Back button + title ───────────────────────────────────────
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("ghostButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setFont(QFont("Segoe UI", 12))
        back_btn.clicked.connect(self.back_requested.emit)
        top_bar.addWidget(back_btn)

        self._title_label = QLabel("")
        self._title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._title_label.setStyleSheet("color: #e6edf3;")
        top_bar.addWidget(self._title_label, 1)
        layout.addLayout(top_bar)

        # ── Metadata bar ─────────────────────────────────────────────
        self._meta_frame = QFrame()
        self._meta_frame.setStyleSheet(
            """
            QFrame {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 12px 18px;
            }
            QLabel { color: #8b949e; font-size: 12px; background: transparent; border: none; }
            """
        )
        meta_layout = QHBoxLayout(self._meta_frame)
        meta_layout.setSpacing(24)

        self._meta_type = QLabel("")
        self._meta_size = QLabel("")
        self._meta_words = QLabel("")
        self._meta_reading = QLabel("")

        for label in (self._meta_type, self._meta_size, self._meta_words, self._meta_reading):
            meta_layout.addWidget(label)
        meta_layout.addStretch()

        layout.addWidget(self._meta_frame)

        # ── Search bar ────────────────────────────────────────────────
        search_bar = QHBoxLayout()
        search_bar.setSpacing(8)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍  Search in document...")
        self._search_input.setMinimumHeight(36)
        self._search_input.setStyleSheet(
            """
            QLineEdit {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                color: #e6edf3;
                padding: 6px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #58a6ff; }
            """
        )
        self._search_input.textChanged.connect(self._highlight_matches)
        search_bar.addWidget(self._search_input, 1)

        self._match_label = QLabel("")
        self._match_label.setStyleSheet("color: #8b949e; font-size: 12px; min-width: 80px;")
        self._match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_bar.addWidget(self._match_label)

        prev_btn = QPushButton("▲")
        prev_btn.setFixedSize(36, 36)
        prev_btn.setObjectName("smallButton")
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.clicked.connect(self._prev_match)
        search_bar.addWidget(prev_btn)

        next_btn = QPushButton("▼")
        next_btn.setFixedSize(36, 36)
        next_btn.setObjectName("smallButton")
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.clicked.connect(self._next_match)
        search_bar.addWidget(next_btn)

        layout.addLayout(search_bar)

        # ── Text area ────────────────────────────────────────────────
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFont(QFont("Consolas", 12))
        self._text_edit.setStyleSheet(
            """
            QTextEdit {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                color: #e6edf3;
                padding: 16px;
                selection-background-color: #264f78;
            }
            QScrollBar:vertical {
                background: #0d1117;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #30363d;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #484f58; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            """
        )
        layout.addWidget(self._text_edit, 1)

    # ── Public API ────────────────────────────────────────────────────

    def load_document(self, doc_id: str):
        """Load and display a document by its ID."""
        doc = self._service.get_document(doc_id)
        if doc is None:
            self._title_label.setText("Document not found")
            self._text_edit.clear()
            return

        self._current_doc = doc
        self._title_label.setText(f"📄  {doc.filename}")
        self._meta_type.setText(f"Type: {doc.file_type.upper().lstrip('.')}")
        self._meta_size.setText(f"Size: {doc.file_size_display}")
        self._meta_words.setText(f"Words: {doc.word_count:,}")
        self._meta_reading.setText(f"Reading: ~{doc.reading_time_minutes} min")

        text = self._service.get_extracted_text(doc_id)
        self._text_edit.setPlainText(text)
        self._search_input.clear()
        self._match_label.setText("")

    # ── In-document search ────────────────────────────────────────────

    def _highlight_matches(self, query: str):
        """Highlight all occurrences of query in the text."""
        # Reset formatting
        cursor = self._text_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        default_fmt = QTextCharFormat()
        default_fmt.setBackground(QColor("transparent"))
        cursor.setCharFormat(default_fmt)
        cursor.clearSelection()

        self._match_positions = []
        self._current_match = -1

        if not query.strip():
            self._match_label.setText("")
            return

        highlight_fmt = QTextCharFormat()
        highlight_fmt.setBackground(QColor("#5e4b00"))
        highlight_fmt.setForeground(QColor("#ffd33d"))

        document = self._text_edit.document()
        cursor = QTextCursor(document)

        while True:
            cursor = document.find(query, cursor)
            if cursor.isNull():
                break
            self._match_positions.append(cursor.position())
            cursor.mergeCharFormat(highlight_fmt)

        count = len(self._match_positions)
        self._match_label.setText(f"{count} match{'es' if count != 1 else ''}")

        if count > 0:
            self._current_match = 0
            self._scroll_to_match(0)

    def _scroll_to_match(self, index: int):
        if not self._match_positions:
            return
        pos = self._match_positions[index]
        cursor = self._text_edit.textCursor()
        cursor.setPosition(pos)
        self._text_edit.setTextCursor(cursor)
        self._text_edit.ensureCursorVisible()
        self._match_label.setText(
            f"{index + 1}/{len(self._match_positions)}"
        )

    def _next_match(self):
        if not self._match_positions:
            return
        self._current_match = (self._current_match + 1) % len(self._match_positions)
        self._scroll_to_match(self._current_match)

    def _prev_match(self):
        if not self._match_positions:
            return
        self._current_match = (self._current_match - 1) % len(self._match_positions)
        self._scroll_to_match(self._current_match)
