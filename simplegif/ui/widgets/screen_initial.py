"""Tela inicial para seleção do arquivo de vídeo."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class InitialScreen(QWidget):
    """Tela de boas-vindas com botão de seleção de vídeo."""

    select_file_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 40, 35, 40)
        layout.setSpacing(15)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(18)

        lbl_icon = QLabel("🎬")
        lbl_icon.setStyleSheet("font-size: 54px;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel("Simple GIF Maker")
        lbl_title.setObjectName("titleLabel")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_sub = QLabel("Conversor de vídeo para GIF 100% offline, rápido e seguro.")
        lbl_sub.setObjectName("subtitleLabel")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_select = QPushButton(" Escolher Arquivo de Vídeo")
        self.btn_select.setObjectName("primaryButton")
        self.btn_select.setFixedHeight(48)
        self.btn_select.setFixedWidth(240)
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.clicked.connect(self.select_file_clicked.emit)

        lbl_formats = QLabel("Formatos suportados: MP4, AVI, MOV, MKV")
        lbl_formats.setObjectName("subtitleLabel")
        lbl_formats.setStyleSheet("font-size: 11px; color: #71717a;")
        lbl_formats.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(lbl_icon)
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_sub)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.btn_select, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_formats)

        layout.addWidget(card)
