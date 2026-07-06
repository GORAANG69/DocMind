"""Dashboard page — landing screen with stats cards and recent documents."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.document_service import DocumentService


class StatCard(QFrame):
    """A single glassmorphism-style stat card."""

    def __init__(self, title: str, value: str, icon_char: str, accent: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setStyleSheet(
            f"""
            #statCard {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 rgba(33,38,45,220), stop:1 rgba(22,27,34,240));
                border: 1px solid #30363d;
                border-radius: 14px;
                padding: 20px;
                min-width: 180px;
            }}
            #statCard:hover {{
                border: 1px solid {accent};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Icon
        icon_label = QLabel(icon_char)
        icon_label.setFont(QFont("Segoe UI Emoji", 28))
        icon_label.setStyleSheet(f"color: {accent}; background: transparent; border: none;")

        # Value
        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self._value_label.setStyleSheet("color: #e6edf3; background: transparent; border: none;")

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11))
        title_label.setStyleSheet("color: #8b949e; background: transparent; border: none;")

        layout.addWidget(icon_label)
        layout.addWidget(self._value_label)
        layout.addWidget(title_label)

    def set_value(self, value: str):
        self._value_label.setText(value)


class DashboardPage(QWidget):
    """Main dashboard with stats, recent docs, and folder actions."""

    select_folder_requested = pyqtSignal()
    refresh_folder_requested = pyqtSignal()
    document_selected = pyqtSignal(str)  # doc_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = DocumentService()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        # ── Header ────────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #e6edf3;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("  Refresh Folder")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        refresh_btn.setMinimumHeight(42)
        refresh_btn.setMinimumWidth(160)
        refresh_btn.clicked.connect(self.refresh_folder_requested.emit)
        header_layout.addWidget(refresh_btn)

        select_folder_btn = QPushButton("  Select Folder")
        select_folder_btn.setObjectName("primaryButton")
        select_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        select_folder_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        select_folder_btn.setMinimumHeight(42)
        select_folder_btn.setMinimumWidth(160)
        select_folder_btn.clicked.connect(self.select_folder_requested.emit)
        header_layout.addWidget(select_folder_btn)
        layout.addLayout(header_layout)

        # ── Stat cards ────────────────────────────────────────────────
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(18)

        self._card_docs = StatCard("Total Documents", "0", "📄", "#58a6ff")
        self._card_words = StatCard("Words Indexed", "0", "📝", "#7ee787")
        self._card_storage = StatCard("Storage Used", "0 B", "💾", "#d2a8ff")

        cards_layout.addWidget(self._card_docs)
        cards_layout.addWidget(self._card_words)
        cards_layout.addWidget(self._card_storage)
        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        # ── Recent documents ──────────────────────────────────────────
        recent_label = QLabel("Recent Documents")
        recent_label.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        recent_label.setStyleSheet("color: #e6edf3;")
        layout.addWidget(recent_label)

        self._recent_list = QListWidget()
        self._recent_list.setObjectName("recentList")
        self._recent_list.setMinimumHeight(200)
        self._recent_list.setStyleSheet(
            """
            QListWidget#recentList {
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 6px;
                color: #e6edf3;
                font-size: 13px;
            }
            QListWidget#recentList::item {
                padding: 10px 14px;
                border-radius: 6px;
            }
            QListWidget#recentList::item:hover {
                background: #21262d;
            }
            QListWidget#recentList::item:selected {
                background: #1f3a5f;
                color: #58a6ff;
            }
            """
        )
        self._recent_list.itemDoubleClicked.connect(self._on_doc_clicked)
        layout.addWidget(self._recent_list, 1)

        # Empty state
        self._empty_label = QLabel("No documents yet. Click 'Select Folder' to get started!")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setFont(QFont("Segoe UI", 13))
        self._empty_label.setStyleSheet("color: #484f58; padding: 40px;")
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)

    def refresh(self):
        """Reload dashboard data from the database."""
        total_docs = self._service.get_total_documents()
        total_words = self._service.get_total_words()
        total_storage = self._service.get_total_storage()

        self._card_docs.set_value(f"{total_docs:,}")
        self._card_words.set_value(f"{total_words:,}")
        self._card_storage.set_value(self._format_size(total_storage))

        recent = self._service.get_recent_documents(10)
        self._recent_list.clear()

        if not recent:
            self._recent_list.setVisible(False)
            self._empty_label.setVisible(True)
        else:
            self._recent_list.setVisible(True)
            self._empty_label.setVisible(False)
            for doc in recent:
                icon_map = {
                    ".pdf": "📕",
                    ".docx": "📘",
                    ".xlsx": "📗",
                    ".xls": "📗",
                    ".txt": "📄",
                }
                icon = icon_map.get(doc.file_type, "📄")
                item = QListWidgetItem(
                    f"{icon}  {doc.filename}    —    {doc.file_size_display}    •    {doc.word_count:,} words"
                )
                item.setData(Qt.ItemDataRole.UserRole, doc.id)
                self._recent_list.addItem(item)

    def _on_doc_clicked(self, item: QListWidgetItem):
        doc_id = item.data(Qt.ItemDataRole.UserRole)
        if doc_id:
            self.document_selected.emit(doc_id)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
