"""Tela de opções e configuração da conversão de vídeo para GIF."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from simplegif.ui.helpers import SCALE_MAP
from simplegif.ui.widgets.video_preview import VideoPreviewWidget


class OptionsScreen(QWidget):
    """Tela de configuração de parâmetros, recorte e estimativa de tamanho do GIF."""

    browse_output_requested = Signal()
    back_requested = Signal()
    start_conversion_requested = Signal()
    options_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 16, 26, 16)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 16, 22, 16)
        card_layout.setSpacing(10)

        # Cabeçalho com título e metadados
        header_row = QHBoxLayout()
        lbl_title = QLabel("Configurar Conversão e Trecho")
        lbl_title.setObjectName("sectionTitle")
        self.lbl_video_meta = QLabel("")
        self.lbl_video_meta.setObjectName("subtitleLabel")
        self.lbl_video_meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(lbl_title)
        header_row.addWidget(self.lbl_video_meta)
        card_layout.addLayout(header_row)

        # Componente de Pré-visualização e Recorte
        self.video_preview = VideoPreviewWidget()
        self.video_preview.range_changed.connect(lambda _s, _e: self.options_changed.emit())
        card_layout.addWidget(self.video_preview)

        # Vídeo de entrada
        card_layout.addWidget(QLabel("Vídeo Selecionado:"))
        self.entry_input_path = QLineEdit()
        self.entry_input_path.setReadOnly(True)
        card_layout.addWidget(self.entry_input_path)

        # Pasta de saída
        card_layout.addWidget(QLabel("Salvar na Pasta:"))
        out_row = QHBoxLayout()
        self.entry_output_dir = QLineEdit()
        self.entry_output_dir.setReadOnly(True)
        self.btn_browse_out = QPushButton("Alterar...")
        self.btn_browse_out.clicked.connect(self.browse_output_requested.emit)
        out_row.addWidget(self.entry_output_dir)
        out_row.addWidget(self.btn_browse_out)
        card_layout.addLayout(out_row)

        # Grade de Opções
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Escala de Tamanho:"), 0, 0)
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(list(SCALE_MAP.keys()))
        self.combo_scale.setCurrentIndex(2)  # 60% (Recomendado)
        self.combo_scale.currentIndexChanged.connect(lambda _idx: self.options_changed.emit())
        grid.addWidget(self.combo_scale, 0, 1)

        grid.addWidget(QLabel("Intervalo de Quadros (Skip):"), 1, 0)
        self.spin_frame_skip = QSpinBox()
        self.spin_frame_skip.setRange(1, 30)
        self.spin_frame_skip.setValue(5)
        self.spin_frame_skip.setSuffix(" quadros")
        self.spin_frame_skip.valueChanged.connect(lambda _val: self.options_changed.emit())
        grid.addWidget(self.spin_frame_skip, 1, 1)

        card_layout.addLayout(grid)

        # Checkboxes
        self.chk_less_colors = QCheckBox("Reduzir paleta de cores (Gera arquivos menores)")
        self.chk_less_colors.setChecked(True)
        self.chk_less_colors.toggled.connect(lambda _checked: self.options_changed.emit())
        card_layout.addWidget(self.chk_less_colors)

        self.chk_overwrite = QCheckBox("Sobrescrever arquivo se já existir")
        self.chk_overwrite.setChecked(False)
        card_layout.addWidget(self.chk_overwrite)

        # Estimativa de Tamanho
        self.lbl_size_estimate = QLabel("📊 Tamanho estimado do GIF: --")
        self.lbl_size_estimate.setObjectName("sizeEstimateLabel")
        self.lbl_size_estimate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_size_estimate)

        layout.addWidget(card)

        # Botões de Ação
        btn_box = QHBoxLayout()
        self.btn_cancel = QPushButton("Voltar")
        self.btn_cancel.setObjectName("secondaryButton")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.clicked.connect(self.back_requested.emit)

        self.btn_start = QPushButton("🚀 Iniciar Conversão")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setFixedHeight(40)
        self.btn_start.clicked.connect(self.start_conversion_requested.emit)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_start)
        layout.addLayout(btn_box)

    def get_selected_scale(self) -> float:
        """Retorna o fator numérico de escala."""
        return SCALE_MAP.get(self.combo_scale.currentText(), 0.6)

    def set_size_estimate_text(self, text: str) -> None:
        """Atualiza a mensagem no badge de estimativa."""
        self.lbl_size_estimate.setText(text)
