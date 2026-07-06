"""Document library — sortable table of all imported documents."""
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
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

    select_folder_requested = pyqtSignal()
    refresh_folder_requested = pyqtSignal()
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

        refresh_btn = QPushButton("  Refresh Folder")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        refresh_btn.setMinimumHeight(42)
        refresh_btn.setMinimumWidth(160)
        refresh_btn.clicked.connect(self.refresh_folder_requested.emit)
        header.addWidget(refresh_btn)

        select_folder_btn = QPushButton("  Select Folder")
        select_folder_btn.setObjectName("primaryButton")
        select_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        select_folder_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        select_folder_btn.setMinimumHeight(42)
        select_folder_btn.setMinimumWidth(160)
        select_folder_btn.clicked.connect(self.select_folder_requested.emit)
        header.addWidget(select_folder_btn)
        layout.addLayout(header)

        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self._delete_btn = QPushButton("🗑️  Delete")
        self._delete_btn.setObjectName("deleteButton")
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.setFont(QFont("Segoe UI", 12))
        self._delete_btn.setMinimumHeight(36)
        self._delete_btn.setEnabled(False)
        self._delete_btn.setStyleSheet(
            """
            QPushButton#deleteButton {
                background: #21262d;
                color: #f85149;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 6px 16px;
            }
            QPushButton#deleteButton:hover {
                background: #3d0c0c;
                border-color: #f85149;
            }
            QPushButton#deleteButton:disabled {
                color: #484f58;
                border-color: #21262d;
            }
            """
        )
        self._delete_btn.clicked.connect(self._delete_selected)
        toolbar.addWidget(self._delete_btn)

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
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

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
        self._empty_label = QLabel(
            "📂  No documents indexed yet.\n\n"
            "Click \"Select Folder\" to begin indexing research papers."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setFont(QFont("Segoe UI", 14))
        self._empty_label.setStyleSheet("color: #484f58; padding: 60px; line-height: 1.6;")
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)

        # ── Keyboard shortcut: Delete key ─────────────────────────────
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self._table)
        delete_shortcut.activated.connect(self._delete_selected)

    # ── Data ──────────────────────────────────────────────────────────

    def refresh(self):
        """Reload all documents from the database."""
        self._docs = self._service.get_all_documents()
        self._apply_sort(self._sort_combo.currentText())
        self._on_selection_changed()  # update delete button state

    def _on_selection_changed(self):
        """Enable/disable delete button based on row selection."""
        has_selection = len(self._table.selectedItems()) > 0
        self._delete_btn.setEnabled(has_selection)

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

        icon_map = {".pdf": "📕", ".docx": "📘", ".xlsx": "📗", ".xls": "📗", ".txt": "📄"}

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

    def _delete_selected(self):
        """Delete the currently selected row (called from toolbar button or Delete key)."""
        rows = self._table.selectedItems()
        if not rows:
            return
        row = self._table.currentRow()
        item = self._table.item(row, 0)
        if not item:
            return
        doc_id = item.data(Qt.ItemDataRole.UserRole)
        if doc_id:
            self._delete_document(doc_id)

    def _delete_document(self, doc_id: str):
        """Show confirmation dialog then delete document and all associated data."""
        doc = self._service.get_document(doc_id)
        if doc is None:
            return

        # ── Confirmation dialog ───────────────────────────────────────
        dlg = QDialog(self)
        dlg.setWindowTitle("Delete Document")
        dlg.setFixedWidth(440)
        dlg.setStyleSheet(
            """
            QDialog {
                background: #161b22;
                border-radius: 12px;
            }
            QLabel {
                background: transparent;
                color: #e6edf3;
            }
            """
        )

        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(28, 24, 28, 24)
        dlg_layout.setSpacing(16)

        # Warning icon + title
        title_row = QHBoxLayout()
        icon_lbl = QLabel("🗑️")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 22))
        icon_lbl.setStyleSheet("background: transparent;")
        title_row.addWidget(icon_lbl)

        title_lbl = QLabel("Delete Document")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #f85149; background: transparent;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        dlg_layout.addLayout(title_row)

        # Message
        msg_lbl = QLabel("Are you sure you want to permanently remove this document from DocMind?")
        msg_lbl.setWordWrap(True)
        msg_lbl.setFont(QFont("Segoe UI", 13))
        msg_lbl.setStyleSheet("color: #8b949e; background: transparent;")
        dlg_layout.addWidget(msg_lbl)

        # Filename
        fname_lbl = QLabel(doc.filename)
        fname_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        fname_lbl.setStyleSheet(
            "color: #e6edf3; background: #21262d; border: 1px solid #30363d;"
            " border-radius: 6px; padding: 8px 12px;"
        )
        fname_lbl.setWordWrap(True)
        dlg_layout.addWidget(fname_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Segoe UI", 13))
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background: #21262d;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 6px 20px;
            }
            QPushButton:hover { background: #30363d; border-color: #484f58; }
            """
        )
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        delete_btn.setMinimumHeight(38)
        delete_btn.setMinimumWidth(100)
        delete_btn.setStyleSheet(
            """
            QPushButton {
                background: #da3633;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 6px 20px;
            }
            QPushButton:hover { background: #f85149; }
            QPushButton:pressed { background: #b91c1c; }
            """
        )
        delete_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(delete_btn)

        dlg_layout.addLayout(btn_row)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        # ── Perform deletion ──────────────────────────────────────────
        try:
            success = self._service.delete_document(doc_id)
        except PermissionError:
            QMessageBox.critical(
                self, "Deletion Failed",
                f"Cannot delete '{doc.filename}'.\n\n"
                "The file appears to be open or locked by another program.\n"
                "Please close it and try again."
            )
            return
        except OSError as exc:
            QMessageBox.critical(
                self, "Deletion Failed",
                f"Could not delete '{doc.filename}':\n\n{exc}"
            )
            return

        if not success:
            QMessageBox.warning(
                self, "Not Found",
                "The document record was not found in the database."
            )
            return

        self.document_deleted.emit(doc_id)
        self.refresh()
