"""Document library — sortable table of all imported documents."""
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.models import Document
from services.document_service import DocumentService


class DocumentLibrary(QWidget):
    """Sortable, filterable document table."""

    import_requested = pyqtSignal()
    document_open = pyqtSignal(str)        # doc_id
    document_stats = pyqtSignal(str)       # doc_id
    document_deleted = pyqtSignal(str)     # doc_id

    _COLUMNS = ["Name", "Type", "Size", "Date Added", "Words"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = DocumentService()
        self._docs: list[Document] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Document Library")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #e6edf3;")
        header.addWidget(title)
        header.addStretch()

        import_btn = QPushButton("  Import Files")
        import_btn.setObjectName("primaryButton")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        import_btn.setMinimumHeight(42)
        import_btn.setMinimumWidth(160)
        import_btn.clicked.connect(self.import_requested.emit)
        header.addWidget(import_btn)
        layout.addLayout(header)

        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("🔍  Filter by filename...")
        self._filter_input.setMinimumHeight(36)
        self._filter_input.setStyleSheet(
            """
            QLineEdit {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                color: #e6edf3;
                padding: 6px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #58a6ff;
            }
            """
        )
        self._filter_input.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self._filter_input, 1)

        sort_label = QLabel("Sort:")
        sort_label.setStyleSheet("color: #8b949e; font-size: 13px;")
        toolbar.addWidget(sort_label)

        self._sort_combo = QComboBox()
        self._sort_combo.addItems(["Name ↑", "Name ↓", "Date ↑", "Date ↓", "Size ↑", "Size ↓", "Type"])
        self._sort_combo.setMinimumHeight(36)
        self._sort_combo.setStyleSheet(
            """
            QComboBox {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                color: #e6edf3;
                padding: 6px 12px;
                font-size: 13px;
                min-width: 110px;
            }
            QComboBox:hover { border: 1px solid #58a6ff; }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
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
        self._sort_combo.currentTextChanged.connect(self._apply_sort)
        toolbar.addWidget(self._sort_combo)

        layout.addLayout(toolbar)

        # ── Table ─────────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels(self._COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)

        header_view = self._table.horizontalHeader()
        header_view.setStretchLastSection(True)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(self._COLUMNS)):
            header_view.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self._table.setStyleSheet(
            """
            QTableWidget {
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 10px;
                color: #e6edf3;
                gridline-color: transparent;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #21262d;
            }
            QTableWidget::item:selected {
                background: #1f3a5f;
                color: #58a6ff;
            }
            QTableWidget::item:hover {
                background: #161b22;
            }
            QHeaderView::section {
                background: #161b22;
                color: #8b949e;
                border: none;
                border-bottom: 2px solid #30363d;
                padding: 10px 12px;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
            }
            """
        )
        layout.addWidget(self._table, 1)

        # Empty state
        self._empty_label = QLabel("📂  Your library is empty.\nImport documents to get started.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setFont(QFont("Segoe UI", 14))
        self._empty_label.setStyleSheet("color: #484f58; padding: 60px;")
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)

    # ── Data ──────────────────────────────────────────────────────────

    def refresh(self):
        """Reload all documents from the database."""
        self._docs = self._service.get_all_documents()
        self._apply_sort(self._sort_combo.currentText())

    def _populate_table(self, docs: list[Document]):
        """Fill the table with the given document list."""
        self._table.setRowCount(0)

        if not docs:
            self._table.setVisible(False)
            self._empty_label.setVisible(True)
            return

        self._table.setVisible(True)
        self._empty_label.setVisible(False)
        self._table.setRowCount(len(docs))

        icon_map = {".pdf": "📕", ".docx": "📘", ".xlsx": "📗", ".txt": "📄"}

        for row, doc in enumerate(docs):
            icon = icon_map.get(doc.file_type, "📄")

            name_item = QTableWidgetItem(f"{icon}  {doc.filename}")
            name_item.setData(Qt.ItemDataRole.UserRole, doc.id)
            self._table.setItem(row, 0, name_item)

            self._table.setItem(row, 1, QTableWidgetItem(doc.file_type.upper().lstrip(".")))
            self._table.setItem(row, 2, QTableWidgetItem(doc.file_size_display))

            try:
                dt = datetime.fromisoformat(doc.created_at)
                date_str = dt.strftime("%b %d, %Y  %H:%M")
            except Exception:
                date_str = doc.created_at
            self._table.setItem(row, 3, QTableWidgetItem(date_str))

            self._table.setItem(row, 4, QTableWidgetItem(f"{doc.word_count:,}"))

    # ── Sorting ───────────────────────────────────────────────────────

    def _apply_sort(self, sort_key: str):
        docs = list(self._docs)
        match sort_key:
            case "Name ↑":
                docs.sort(key=lambda d: d.filename.lower())
            case "Name ↓":
                docs.sort(key=lambda d: d.filename.lower(), reverse=True)
            case "Date ↑":
                docs.sort(key=lambda d: d.created_at)
            case "Date ↓":
                docs.sort(key=lambda d: d.created_at, reverse=True)
            case "Size ↑":
                docs.sort(key=lambda d: d.file_size)
            case "Size ↓":
                docs.sort(key=lambda d: d.file_size, reverse=True)
            case "Type":
                docs.sort(key=lambda d: d.file_type)
        self._populate_table(docs)
        self._apply_filter(self._filter_input.text())

    def _apply_filter(self, text: str):
        query = text.lower().strip()
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            visible = query in item.text().lower() if item else True
            self._table.setRowHidden(row, not visible)

    # ── Context menu ──────────────────────────────────────────────────

    def _show_context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return

        item = self._table.item(row, 0)
        doc_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not doc_id:
            return

        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 4px;
                color: #e6edf3;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected { background: #1f3a5f; }
            """
        )

        open_action = QAction("📖  Open", self)
        open_action.triggered.connect(lambda: self.document_open.emit(doc_id))
        menu.addAction(open_action)

        stats_action = QAction("📊  View Statistics", self)
        stats_action.triggered.connect(lambda: self.document_stats.emit(doc_id))
        menu.addAction(stats_action)

        menu.addSeparator()

        delete_action = QAction("🗑️  Delete", self)
        delete_action.triggered.connect(lambda: self._delete_document(doc_id))
        menu.addAction(delete_action)

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_double_click(self, index):
        row = index.row()
        item = self._table.item(row, 0)
        if item:
            doc_id = item.data(Qt.ItemDataRole.UserRole)
            if doc_id:
                self.document_open.emit(doc_id)

    def _delete_document(self, doc_id: str):
        self._service.delete_document(doc_id)
        self.document_deleted.emit(doc_id)
        self.refresh()
