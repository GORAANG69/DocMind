"""Statistics panel — per-document analytics with keyword chart."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.document_service import DocumentService
from services.statistics_service import StatisticsService


class KeywordBar(QWidget):
    """Custom-painted horizontal bar for a single keyword."""

    def __init__(self, word: str, count: int, max_count: int, parent=None):
        super().__init__(parent)
        self._word = word
        self._count = count
        self._ratio = count / max_count if max_count > 0 else 0
        self.setMinimumHeight(28)
        self.setMaximumHeight(28)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#21262d"))
        painter.drawRoundedRect(0, 0, w, h, 6, 6)

        # Bar fill
        bar_width = int((w - 160) * self._ratio)
        if bar_width > 0:
            gradient_color = QColor("#58a6ff")
            gradient_color.setAlpha(180)
            painter.setBrush(gradient_color)
            painter.drawRoundedRect(150, 2, bar_width, h - 4, 4, 4)

        # Text
        painter.setPen(QPen(QColor("#e6edf3")))
        font = QFont("Segoe UI", 11)
        painter.setFont(font)
        painter.drawText(10, 0, 130, h, Qt.AlignmentFlag.AlignVCenter, self._word)

        # Count
        painter.setPen(QPen(QColor("#8b949e")))
        painter.drawText(
            150 + bar_width + 8, 0, 60, h,
            Qt.AlignmentFlag.AlignVCenter, str(self._count)
        )
        painter.end()


class StatisticsPanel(QWidget):
    """Per-document statistics display with keyword chart."""

    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = DocumentService()
        self._current_doc_id: str | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("📊  Statistics")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #e6edf3;")
        header.addWidget(title)
        header.addStretch()

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.setObjectName("secondaryButton")
        self._export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._export_btn.setFont(QFont("Segoe UI", 11))
        self._export_btn.setMinimumHeight(38)
        self._export_btn.clicked.connect(self._export_csv)
        self._export_btn.setEnabled(False)
        header.addWidget(self._export_btn)
        layout.addLayout(header)

        # ── Document selector ─────────────────────────────────────────
        selector_layout = QHBoxLayout()
        sel_label = QLabel("Select document:")
        sel_label.setStyleSheet("color: #8b949e; font-size: 13px;")
        selector_layout.addWidget(sel_label)

        self._doc_combo = QComboBox()
        self._doc_combo.setMinimumHeight(38)
        self._doc_combo.setMinimumWidth(400)
        self._doc_combo.setStyleSheet(
            """
            QComboBox {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                color: #e6edf3;
                padding: 6px 12px;
                font-size: 13px;
            }
            QComboBox:hover { border: 1px solid #58a6ff; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #8b949e;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: #161b22;
                border: 1px solid #30363d;
                color: #e6edf3;
                selection-background-color: #1f3a5f;
            }
            """
        )
        self._doc_combo.currentIndexChanged.connect(self._on_doc_selected)
        selector_layout.addWidget(self._doc_combo, 1)
        layout.addLayout(selector_layout)

        # ── Stat cards row ────────────────────────────────────────────
        cards = QHBoxLayout()
        cards.setSpacing(14)

        self._stat_labels: dict[str, QLabel] = {}
        stat_defs = [
            ("Words", "📝", "#58a6ff"),
            ("Unique", "🔤", "#7ee787"),
            ("Characters", "🔡", "#d2a8ff"),
            ("Lines", "📃", "#ffa657"),
            ("Reading Time", "⏱️", "#f778ba"),
        ]
        for name, icon, accent in stat_defs:
            card = QFrame()
            card.setStyleSheet(
                f"""
                QFrame {{
                    background: #161b22;
                    border: 1px solid #30363d;
                    border-radius: 12px;
                    padding: 14px;
                }}
                QFrame:hover {{ border-color: {accent}; }}
                """
            )
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(4)

            icon_l = QLabel(icon)
            icon_l.setFont(QFont("Segoe UI Emoji", 18))
            icon_l.setStyleSheet("background: transparent; border: none;")
            card_layout.addWidget(icon_l)

            val_l = QLabel("—")
            val_l.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            val_l.setStyleSheet(f"color: {accent}; background: transparent; border: none;")
            card_layout.addWidget(val_l)
            self._stat_labels[name] = val_l

            name_l = QLabel(name)
            name_l.setFont(QFont("Segoe UI", 10))
            name_l.setStyleSheet("color: #8b949e; background: transparent; border: none;")
            card_layout.addWidget(name_l)

            cards.addWidget(card)

        layout.addLayout(cards)

        # ── Keywords section ──────────────────────────────────────────
        kw_label = QLabel("Top Keywords")
        kw_label.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        kw_label.setStyleSheet("color: #e6edf3;")
        layout.addWidget(kw_label)

        self._keywords_container = QVBoxLayout()
        self._keywords_container.setSpacing(4)

        kw_frame = QFrame()
        kw_frame.setStyleSheet(
            """
            QFrame {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 12px;
            }
            """
        )
        kw_frame.setLayout(self._keywords_container)
        layout.addWidget(kw_frame, 1)

    # ── Public API ────────────────────────────────────────────────────

    def refresh(self):
        """Reload the document selector."""
        self._doc_combo.blockSignals(True)
        self._doc_combo.clear()
        self._doc_combo.addItem("— Select a document —", None)

        docs = self._service.get_all_documents()
        icon_map = {".pdf": "📕", ".docx": "📘", ".xlsx": "📗", ".txt": "📄"}
        for doc in docs:
            icon = icon_map.get(doc.file_type, "📄")
            self._doc_combo.addItem(f"{icon}  {doc.filename}", doc.id)

        self._doc_combo.blockSignals(False)

        # Re-select current doc if still present
        if self._current_doc_id:
            idx = self._doc_combo.findData(self._current_doc_id)
            if idx >= 0:
                self._doc_combo.setCurrentIndex(idx)

    def load_document(self, doc_id: str):
        """Load stats for a specific document."""
        self._current_doc_id = doc_id
        self.refresh()
        idx = self._doc_combo.findData(doc_id)
        if idx >= 0:
            self._doc_combo.setCurrentIndex(idx)

    # ── Slots ─────────────────────────────────────────────────────────

    def _on_doc_selected(self, index: int):
        doc_id = self._doc_combo.itemData(index)
        if doc_id is None:
            self._clear_stats()
            return

        self._current_doc_id = doc_id
        self._export_btn.setEnabled(True)

        text = self._service.get_extracted_text(doc_id)
        stats = StatisticsService.compute(text)

        self._stat_labels["Words"].setText(f"{stats['word_count']:,}")
        self._stat_labels["Unique"].setText(f"{stats['unique_words']:,}")
        self._stat_labels["Characters"].setText(f"{stats['char_count']:,}")
        self._stat_labels["Lines"].setText(f"{stats['line_count']:,}")
        self._stat_labels["Reading Time"].setText(f"{stats['reading_time_min']} min")

        # Keyword bars
        self._clear_keywords()
        keywords = stats["top_keywords"]
        if keywords:
            max_count = keywords[0][1]
            for word, count in keywords:
                bar = KeywordBar(word, count, max_count)
                self._keywords_container.addWidget(bar)
        self._keywords_container.addStretch()

    def _clear_stats(self):
        self._export_btn.setEnabled(False)
        for label in self._stat_labels.values():
            label.setText("—")
        self._clear_keywords()

    def _clear_keywords(self):
        while self._keywords_container.count():
            item = self._keywords_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _export_csv(self):
        if not self._current_doc_id:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Statistics CSV", "statistics.csv",
            "CSV Files (*.csv)"
        )
        if path:
            from pathlib import Path
            self._service.export_statistics_csv(self._current_doc_id, Path(path))
