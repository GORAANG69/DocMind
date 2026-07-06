"""Search panel — global full-text search across all documents."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

    document_open = pyqtSignal(str, str, object, object, object)  # doc_id, query, page, sheet, cell

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_service = SearchService()
        self._current_results = []
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
        opts_layout.setSpacing(14)

        # Search Mode
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        opts_layout.addWidget(mode_label)

        self._search_mode_combo = QComboBox()
        self._search_mode_combo.addItems(["Exact Phrase", "Keywords"])
        self._search_mode_combo.setMinimumHeight(30)
        self._search_mode_combo.setStyleSheet(
            """
            QComboBox {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #e6edf3;
                padding: 4px 10px;
                font-size: 12px;
                min-width: 100px;
            }
            QComboBox:hover { border: 1px solid #58a6ff; }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox::down-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #8b949e;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background: #161b22;
                border: 1px solid #30363d;
                color: #e6edf3;
                selection-background-color: #1f3a5f;
            }
            """
        )
        opts_layout.addWidget(self._search_mode_combo)

        # Case check
        self._case_check = QCheckBox("Case sensitive")
        self._case_check.setStyleSheet(
            "QCheckBox { color: #8b949e; font-size: 12px; } "
            "QCheckBox::indicator { width: 16px; height: 16px; }"
        )
        opts_layout.addWidget(self._case_check)

        # Whole word check
        self._whole_word_check = QCheckBox("Whole word")
        self._whole_word_check.setStyleSheet(
            "QCheckBox { color: #8b949e; font-size: 12px; } "
            "QCheckBox::indicator { width: 16px; height: 16px; }"
        )
        opts_layout.addWidget(self._whole_word_check)

        opts_layout.addStretch()

        # Sort Order
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        opts_layout.addWidget(sort_label)

        self._sort_combo = QComboBox()
        self._sort_combo.addItems([
            "Matches (High to Low)",
            "Matches (Low to High)",
            "Filename (A to Z)",
            "Filename (Z to A)"
        ])
        self._sort_combo.setMinimumHeight(30)
        self._sort_combo.setStyleSheet(
            """
            QComboBox {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #e6edf3;
                padding: 4px 10px;
                font-size: 12px;
                min-width: 140px;
            }
            QComboBox:hover { border: 1px solid #58a6ff; }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox::down-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #8b949e;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background: #161b22;
                border: 1px solid #30363d;
                color: #e6edf3;
                selection-background-color: #1f3a5f;
            }
            """
        )
        self._sort_combo.currentTextChanged.connect(self._apply_sort)
        opts_layout.addWidget(self._sort_combo)

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

        exact_phrase = self._search_mode_combo.currentText() == "Exact Phrase"
        self._current_results = self._search_service.search(
            query,
            case_sensitive=self._case_check.isChecked(),
            whole_word=self._whole_word_check.isChecked(),
            exact_phrase=exact_phrase,
        )
        self._apply_sort(self._sort_combo.currentText())

    def _apply_sort(self, sort_key: str):
        if not self._current_results:
            self._results_list.clear()
            self._results_list.setVisible(False)
            self._empty_label.setVisible(True)
            self._result_count_label.setText("0 matches")
            return

        results = list(self._current_results)
        if sort_key == "Matches (High to Low)":
            results.sort(key=lambda r: r.match_count, reverse=True)
        elif sort_key == "Matches (Low to High)":
            results.sort(key=lambda r: r.match_count)
        elif sort_key == "Filename (A to Z)":
            results.sort(key=lambda d: d.filename.lower())
        elif sort_key == "Filename (Z to A)":
            results.sort(key=lambda d: d.filename.lower(), reverse=True)

        self._display_results(results)

    def _display_results(self, results: list):
        self._results_list.clear()
        self._empty_label.setVisible(False)
        self._results_list.setVisible(True)

        total_matches = sum(r.match_count for r in results)
        self._result_count_label.setText(
            f"{total_matches} match{'es' if total_matches != 1 else ''} "
            f"in {len(results)} document{'s' if len(results) != 1 else ''}"
        )

        icon_map = {
            ".pdf": "📕",
            ".docx": "📘",
            ".xlsx": "📗",
            ".xls": "📗",
            ".txt": "📄"
        }

        for result in results:
            icon = icon_map.get(result.file_type, "📄")
            
            if result.page_number is not None:
                loc_str = f"Page {result.page_number}"
            elif result.sheet_name is not None:
                loc_str = f"Sheet: {result.sheet_name}, Cell: {result.cell_ref}"
            else:
                loc_str = ""

            loc_part = f"    —    {loc_str}" if loc_str else ""
            
            item_text = (
                f"{icon}  {result.filename}{loc_part}    —    {result.match_count} match"
                f"{'es' if result.match_count != 1 else ''}\n"
                f"      \"{result.snippet}\""
            )
            item = QListWidgetItem(item_text)
            
            # Save coordinates
            coord_data = {
                "doc_id": result.doc_id,
                "page_number": result.page_number,
                "sheet_name": result.sheet_name,
                "cell_ref": result.cell_ref
            }
            item.setData(Qt.ItemDataRole.UserRole, coord_data)
            self._results_list.addItem(item)

    def _on_result_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            query = self._search_input.text().strip()
            self.document_open.emit(
                data["doc_id"],
                query,
                data.get("page_number"),
                data.get("sheet_name"),
                data.get("cell_ref")
            )

    def focus_search(self):
        """Focus the search input field."""
        self._search_input.setFocus()
        self._search_input.selectAll()

    def clear_results_for(self, doc_id: str):
        """Remove any search results belonging to the deleted document."""
        if not self._current_results:
            return

        self._current_results = [
            r for r in self._current_results if r.doc_id != doc_id
        ]

        # Refresh the displayed list
        self._apply_sort(self._sort_combo.currentText())
