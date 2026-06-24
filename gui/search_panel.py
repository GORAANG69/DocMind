"""Search panel — global full-text search across all documents."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.search_service import SearchService


class SearchPanel(QWidget):
    """Global search page with options and results list."""

    document_open = pyqtSignal(str)  # doc_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_service = SearchService()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────
        title = QLabel("🔍  Search Documents")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #e6edf3;")
        layout.addWidget(title)

        # ── Search input ──────────────────────────────────────────────
        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to search across all documents...")
        self._search_input.setMinimumHeight(44)
        self._search_input.setFont(QFont("Segoe UI", 14))
        self._search_input.setStyleSheet(
            """
            QLineEdit {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                color: #e6edf3;
                padding: 8px 16px;
            }
            QLineEdit:focus { border: 1px solid #58a6ff; }
            """
        )
        self._search_input.returnPressed.connect(self._do_search)
        search_row.addWidget(self._search_input, 1)

        search_btn = QPushButton("Search")
        search_btn.setObjectName("primaryButton")
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        search_btn.setMinimumHeight(44)
        search_btn.setMinimumWidth(120)
        search_btn.clicked.connect(self._do_search)
        search_row.addWidget(search_btn)

        layout.addLayout(search_row)

        # ── Options ───────────────────────────────────────────────────
        opts_layout = QHBoxLayout()
        opts_layout.setSpacing(20)

        self._case_check = QCheckBox("Case sensitive")
        self._case_check.setStyleSheet(
            "QCheckBox { color: #8b949e; font-size: 12px; } "
            "QCheckBox::indicator { width: 16px; height: 16px; }"
        )
        opts_layout.addWidget(self._case_check)

        self._whole_word_check = QCheckBox("Whole word")
        self._whole_word_check.setStyleSheet(
            "QCheckBox { color: #8b949e; font-size: 12px; } "
            "QCheckBox::indicator { width: 16px; height: 16px; }"
        )
        opts_layout.addWidget(self._whole_word_check)

        opts_layout.addStretch()

        self._result_count_label = QLabel("")
        self._result_count_label.setStyleSheet("color: #8b949e; font-size: 13px;")
        opts_layout.addWidget(self._result_count_label)

        layout.addLayout(opts_layout)

        # ── Results ───────────────────────────────────────────────────
        self._results_list = QListWidget()
        self._results_list.setStyleSheet(
            """
            QListWidget {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 6px;
                color: #e6edf3;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-radius: 8px;
                margin-bottom: 4px;
            }
            QListWidget::item:hover { background: #161b22; }
            QListWidget::item:selected {
                background: #1f3a5f;
                color: #58a6ff;
            }
            """
        )
        self._results_list.itemDoubleClicked.connect(self._on_result_clicked)
        layout.addWidget(self._results_list, 1)

        # Empty state
        self._empty_label = QLabel("Enter a search query above to find text across all your documents.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setFont(QFont("Segoe UI", 13))
        self._empty_label.setStyleSheet("color: #484f58; padding: 60px;")
        layout.addWidget(self._empty_label)

    # ── Search logic ──────────────────────────────────────────────────

    def _do_search(self):
        query = self._search_input.text().strip()
        if not query:
            return

        results = self._search_service.search(
            query,
            case_sensitive=self._case_check.isChecked(),
            whole_word=self._whole_word_check.isChecked(),
        )

        self._results_list.clear()

        if results:
            self._empty_label.setVisible(False)
            self._results_list.setVisible(True)
            total_matches = sum(r.match_count for r in results)
            self._result_count_label.setText(
                f"{total_matches} match{'es' if total_matches != 1 else ''} "
                f"in {len(results)} document{'s' if len(results) != 1 else ''}"
            )

            for result in results:
                item_text = (
                    f"📄  {result.filename}    —    {result.match_count} match"
                    f"{'es' if result.match_count != 1 else ''}\n"
                    f"      \"{result.snippet}\""
                )
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, result.doc_id)
                self._results_list.addItem(item)
        else:
            self._results_list.setVisible(False)
            self._empty_label.setVisible(True)
            self._empty_label.setText(f"No results found for \"{query}\".")
            self._result_count_label.setText("0 matches")

    def _on_result_clicked(self, item: QListWidgetItem):
        doc_id = item.data(Qt.ItemDataRole.UserRole)
        if doc_id:
            self.document_open.emit(doc_id)

    def focus_search(self):
        """Focus the search input field."""
        self._search_input.setFocus()
        self._search_input.selectAll()
