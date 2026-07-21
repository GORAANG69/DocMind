"""Search panel — global full-text search across all documents.

Results are displayed grouped by document using a QTreeWidget.
Each document is a top-level node; individual page/sheet/cell hits
are expandable children.

Search state (query + options) is persisted to SQLite settings so
it survives application restarts.
"""
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.db_manager import DatabaseManager
from services.search_service import GroupedSearchResult, SearchService


class SearchPanel(QWidget):
    """Global search page with options and grouped results tree."""

    document_open = pyqtSignal(str, str, object, object, object)  # doc_id, query, page, sheet, cell

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_service = SearchService()
        self._db = DatabaseManager()
        self._current_results: list[GroupedSearchResult] = []
        self._setup_ui()
        self._restore_search_state()

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
        self._search_debounce_timer = QTimer(self)
        self._search_debounce_timer.setSingleShot(True)
        self._search_debounce_timer.timeout.connect(self._do_search)

        self._search_input.returnPressed.connect(self._on_return_pressed)
        self._search_input.textChanged.connect(self._on_text_changed)
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
        self._case_check.setStyleSheet("QCheckBox { color: #8b949e; font-size: 12px; }")
        self._case_check.toggled.connect(self._on_return_pressed)
        opts_layout.addWidget(self._case_check)

        # Whole word check
        self._whole_word_check = QCheckBox("Whole word")
        self._whole_word_check.setStyleSheet("QCheckBox { color: #8b949e; font-size: 12px; }")
        self._whole_word_check.toggled.connect(self._on_return_pressed)
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
        self._search_mode_combo.currentTextChanged.connect(self._on_return_pressed)
        self._sort_combo.currentTextChanged.connect(self._apply_sort)
        opts_layout.addWidget(self._sort_combo)

        self._result_count_label = QLabel("")
        self._result_count_label.setStyleSheet("color: #8b949e; font-size: 13px;")
        opts_layout.addWidget(self._result_count_label)

        layout.addLayout(opts_layout)

        # ── Results tree (grouped by document) ────────────────────────
        self._results_tree = QTreeWidget()
        self._results_tree.setHeaderLabels(["Document / Location", "Matches", "Snippet"])
        self._results_tree.setColumnCount(3)
        self._results_tree.setAlternatingRowColors(False)
        self._results_tree.setRootIsDecorated(True)
        self._results_tree.setAnimated(True)
        self._results_tree.setStyleSheet(
            """
            QTreeWidget {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 6px;
                color: #e6edf3;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 8px 10px;
                border-radius: 6px;
            }
            QTreeWidget::item:hover { background: #161b22; }
            QTreeWidget::item:selected {
                background: #1f3a5f;
                color: #58a6ff;
            }
            QHeaderView::section {
                background: #161b22;
                color: #8b949e;
                border: none;
                border-bottom: 1px solid #30363d;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 600;
            }
            """
        )
        self._results_tree.itemDoubleClicked.connect(self._on_result_clicked)
        header = self._results_tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._results_tree, 1)

        # Empty state
        self._empty_label = QLabel("Enter a search query above to find text across all your documents.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setFont(QFont("Segoe UI", 13))
        self._empty_label.setStyleSheet("color: #484f58; padding: 60px;")
        layout.addWidget(self._empty_label)

    # ── Search persistence ────────────────────────────────────────────

    def _save_search_state(self):
        """Persist the current search query and options to the database."""
        query = self._search_input.text().strip()
        self._db.set_setting("search_last_query", query)
        self._db.set_setting("search_mode", self._search_mode_combo.currentText())
        self._db.set_setting("search_case_sensitive", "1" if self._case_check.isChecked() else "0")
        self._db.set_setting("search_whole_word", "1" if self._whole_word_check.isChecked() else "0")

    def _restore_search_state(self):
        """Restore the last search query and options from the database, and re-run the search."""
        query = self._db.get_setting("search_last_query") or ""
        mode = self._db.get_setting("search_mode") or "Exact Phrase"
        case_sensitive = (self._db.get_setting("search_case_sensitive") or "0") == "1"
        whole_word = (self._db.get_setting("search_whole_word") or "0") == "1"

        self._search_input.setText(query)
        idx = self._search_mode_combo.findText(mode)
        if idx >= 0:
            self._search_mode_combo.setCurrentIndex(idx)
        self._case_check.setChecked(case_sensitive)
        self._whole_word_check.setChecked(whole_word)

        # Re-execute the search silently if there was a previous query
        if query:
            self._do_search()

    # ── Search logic ──────────────────────────────────────────────────

    def _on_text_changed(self, text: str):
        if not text.strip():
            self._search_debounce_timer.stop()
            self._do_search()
        else:
            self._search_debounce_timer.stop()
            self._search_debounce_timer.start(300)

    def _on_return_pressed(self):
        self._search_debounce_timer.stop()
        self._do_search()

    def _do_search(self):
        query = self._search_input.text().strip()
        if not query:
            self._current_results = []
            self._results_tree.clear()
            self._results_tree.setVisible(False)
            self._empty_label.setVisible(True)
            self._result_count_label.setText("0 matches")
            self._save_search_state()
            return

        exact_phrase = self._search_mode_combo.currentText() == "Exact Phrase"
        self._current_results = self._search_service.search(
            query,
            case_sensitive=self._case_check.isChecked(),
            whole_word=self._whole_word_check.isChecked(),
            exact_phrase=exact_phrase,
        )
        self._save_search_state()
        self._apply_sort(self._sort_combo.currentText())

    def _apply_sort(self, sort_key: str):
        if not self._current_results:
            self._results_tree.clear()
            self._results_tree.setVisible(False)
            self._empty_label.setVisible(True)
            self._result_count_label.setText("0 matches")
            return

        results = list(self._current_results)
        if sort_key == "Matches (High to Low)":
            results.sort(key=lambda r: r.total_matches, reverse=True)
        elif sort_key == "Matches (Low to High)":
            results.sort(key=lambda r: r.total_matches)
        elif sort_key == "Filename (A to Z)":
            results.sort(key=lambda d: d.filename.lower())
        elif sort_key == "Filename (Z to A)":
            results.sort(key=lambda d: d.filename.lower(), reverse=True)

        self._display_results(results)

    def _display_results(self, results: list[GroupedSearchResult]):
        self._results_tree.clear()
        self._empty_label.setVisible(False)
        self._results_tree.setVisible(True)

        total_matches = sum(r.total_matches for r in results)
        self._result_count_label.setText(
            f"{total_matches} match{'es' if total_matches != 1 else ''} "
            f"in {len(results)} document{'s' if len(results) != 1 else ''}"
        )

        icon_map = {
            ".pdf": "📕",
            ".docx": "📘",
            ".xlsx": "📗",
            ".xls": "📗",
            ".txt": "📄",
            ".csv": "📊",
            ".json": "📋",
        }

        for result in results:
            icon = icon_map.get(result.file_type, "📄")
            display_name = result.original_filename or result.filename

            # Build location summary
            if result.pages:
                loc = f"across {len(result.pages)} page{'s' if len(result.pages) != 1 else ''}"
            elif result.sheets:
                loc = f"in {len(result.sheets)} cell{'s' if len(result.sheets) != 1 else ''}"
            else:
                loc = ""

            doc_label = f"{icon}  {display_name}"
            if loc:
                doc_label += f"    —    {loc}"

            # Top-level item for the document
            doc_item = QTreeWidgetItem([
                doc_label,
                str(result.total_matches),
                result.snippet if result.snippet else "",
            ])
            doc_item.setFont(0, QFont("Segoe UI", 12, QFont.Weight.DemiBold))
            doc_item.setFont(1, QFont("Segoe UI", 11, QFont.Weight.Bold))

            # Attach coordinates for double-click navigation
            doc_item.setData(0, Qt.ItemDataRole.UserRole, {
                "doc_id": result.doc_id,
                "page_number": result.pages[0].page_number if result.pages else None,
                "sheet_name": result.sheets[0].sheet_name if result.sheets else None,
                "cell_ref": result.sheets[0].cell_ref if result.sheets else None,
            })

            # ── Child items: page-level hits (PDF) ────────────────────
            for page in result.pages:
                child = QTreeWidgetItem([
                    f"    📄  Page {page.page_number}",
                    str(page.match_count),
                    f'"{page.snippet}"' if page.snippet else "",
                ])
                child.setData(0, Qt.ItemDataRole.UserRole, {
                    "doc_id": result.doc_id,
                    "page_number": page.page_number,
                    "sheet_name": None,
                    "cell_ref": None,
                })
                doc_item.addChild(child)

            # ── Child items: sheet/cell-level hits (Excel/CSV) ────────
            for sheet in result.sheets:
                child = QTreeWidgetItem([
                    f"    📊  {sheet.sheet_name} [{sheet.cell_ref}]",
                    str(sheet.match_count),
                    f'"{sheet.snippet}"' if sheet.snippet else "",
                ])
                child.setData(0, Qt.ItemDataRole.UserRole, {
                    "doc_id": result.doc_id,
                    "page_number": None,
                    "sheet_name": sheet.sheet_name,
                    "cell_ref": sheet.cell_ref,
                })
                doc_item.addChild(child)

            self._results_tree.addTopLevelItem(doc_item)

            # Auto-expand documents with a small number of child hits
            if doc_item.childCount() <= 10:
                doc_item.setExpanded(True)

    def _on_result_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            query = self._search_input.text().strip()
            self.document_open.emit(
                data["doc_id"],
                query,
                data.get("page_number"),
                data.get("sheet_name"),
                data.get("cell_ref"),
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
