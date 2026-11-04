"""Tela de resultado da conversão de vídeo para GIF."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ResultScreen(QWidget):
    """Tela de exibição do status final (sucesso ou falha) e ações pós-conversão."""

    copy_path_requested = Signal()
    open_folder_requested = Signal()
    new_file_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 30, 35, 30)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_res_icon = QLabel("✅")
        self.lbl_res_icon.setStyleSheet("font-size: 46px;")
        self.lbl_res_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_res_title = QLabel("Concluído!")
        self.lbl_res_title.setObjectName("titleLabel")
        self.lbl_res_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_res_desc = QLabel("Arquivo salvo em:")
        self.lbl_res_desc.setObjectName("subtitleLabel")
        self.lbl_res_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Container do caminho de saída
        self.path_box = QHBoxLayout()
        self.entry_res_path = QLineEdit()
        self.entry_res_path.setReadOnly(True)
        self.btn_copy = QPushButton("Copiar")
        self.btn_copy.clicked.connect(self.copy_path_requested.emit)
        self.path_box.addWidget(self.entry_res_path)
        self.path_box.addWidget(self.btn_copy)

        self.btn_open_folder = QPushButton("📁 Abrir Pasta de Destino")
        self.btn_open_folder.clicked.connect(self.open_folder_requested.emit)
        self.btn_open_folder.setFixedHeight(38)

        self.btn_new_file = QPushButton("Converter Novo Vídeo")
        self.btn_new_file.setObjectName("primaryButton")
        self.btn_new_file.setFixedHeight(42)
        self.btn_new_file.setFixedWidth(200)
        self.btn_new_file.clicked.connect(self.new_file_requested.emit)

        card_layout.addWidget(self.lbl_res_icon)
        card_layout.addWidget(self.lbl_res_title)
        card_layout.addWidget(self.lbl_res_desc)
        card_layout.addLayout(self.path_box)
        card_layout.addWidget(self.btn_open_folder, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.btn_new_file, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card)

    def show_result(
        self,
        success: bool,
        gif_path: Path | None = None,
        error_msg: str = "",
        is_file_exists: bool = False,
    ) -> None:
        """Configura os elementos visuais para sucesso ou falha."""
        if success and gif_path:
            self.lbl_res_icon.setText("✅")
            self.lbl_res_title.setText("GIF Gerado com Sucesso!")
            self.lbl_res_title.setStyleSheet("color: #10b981; font-size: 20px; font-weight: bold;")
            self.lbl_res_desc.setText("Arquivo disponível em:")
            self.entry_res_path.setVisible(True)
            self.entry_res_path.setText(str(gif_path))
            self.btn_copy.setVisible(True)
            self.btn_open_folder.setVisible(True)
        else:
            self.lbl_res_icon.setText("❌")
            self.lbl_res_title.setText("Falha na Conversão")
            self.lbl_res_title.setStyleSheet("color: #ef4444; font-size: 20px; font-weight: bold;")
            self.lbl_res_desc.setText(error_msg)
            self.entry_res_path.setVisible(False)
            self.btn_copy.setVisible(False)
            self.btn_open_folder.setVisible(is_file_exists)
