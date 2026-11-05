"""Tela de opções e configuração em layout widescreen de duas colunas."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from simplegif.ui.helpers import SCALE_MAP
from simplegif.ui.widgets.video_preview import VideoPreviewWidget


class OptionsScreen(QWidget):
    """Interface principal Widescreen em tela única dividida em visualização e configurações."""

    select_file_requested = Signal()
    browse_output_requested = Signal()
    start_conversion_requested = Signal()
    open_folder_requested = Signal()
    options_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # =====================================================================
        # Painel Esquerdo (60% a 65% da largura) — Visualização e Corte
        # =====================================================================
        left_card = QFrame()
        left_card.setObjectName("cardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)

        # Cabeçalho: Título e Metadados do Vídeo
        header_row = QHBoxLayout()
        lbl_title = QLabel("Configurar Conversão")
        lbl_title.setObjectName("sectionTitle")

        self.lbl_video_meta = QLabel("")
        self.lbl_video_meta.setObjectName("subtitleLabel")
        self.lbl_video_meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header_row.addWidget(lbl_title)
        header_row.addWidget(self.lbl_video_meta)
        left_layout.addLayout(header_row)

        # Área de Preview e Controles de Trecho (Expansível em 16:9)
        self.video_preview = VideoPreviewWidget()
        self.video_preview.range_changed.connect(lambda _s, _e: self.options_changed.emit())
        self.video_preview.time_range_changed.connect(lambda _s, _e: self.options_changed.emit())
        left_layout.addWidget(self.video_preview, stretch=1)

        main_layout.addWidget(left_card, stretch=63)

        # =====================================================================
        # Painel Direito (35% a 40% da largura) — Configurações e Ação
        # =====================================================================
        right_card = QFrame()
        right_card.setObjectName("cardFrame")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 16, 18, 16)
        right_layout.setSpacing(12)

        # 1. Vídeo Selecionado
        lbl_in = QLabel("Vídeo Selecionado:")
        lbl_in.setObjectName("sectionTitle")
        in_row = QHBoxLayout()
        in_row.setSpacing(8)

        self.entry_input_path = QLineEdit()
        self.entry_input_path.setReadOnly(True)
        self.entry_input_path.setPlaceholderText("Nenhum vídeo selecionado...")

        self.btn_select_file = QPushButton("Selecionar...")
        self.btn_select_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select_file.setFixedHeight(34)
        self.btn_select_file.clicked.connect(self.select_file_requested.emit)

        in_row.addWidget(self.entry_input_path, stretch=1)
        in_row.addWidget(self.btn_select_file)
        right_layout.addWidget(lbl_in)
        right_layout.addLayout(in_row)

        # 2. Salvar na Pasta
        lbl_out = QLabel("Salvar na Pasta:")
        lbl_out.setObjectName("sectionTitle")
        out_row = QHBoxLayout()
        out_row.setSpacing(8)

        self.entry_output_dir = QLineEdit()
        self.entry_output_dir.setReadOnly(True)
        self.entry_output_dir.setPlaceholderText("Selecione a pasta de saída...")

        self.btn_browse_out = QPushButton("Alterar...")
        self.btn_browse_out.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_out.setFixedHeight(34)
        self.btn_browse_out.clicked.connect(self.browse_output_requested.emit)

        out_row.addWidget(self.entry_output_dir, stretch=1)
        out_row.addWidget(self.btn_browse_out)
        right_layout.addWidget(lbl_out)
        right_layout.addLayout(out_row)

        # 3. Nome do GIF
        lbl_name = QLabel("Nome do GIF:")
        lbl_name.setObjectName("sectionTitle")
        name_row = QHBoxLayout()
        name_row.setSpacing(6)

        self.entry_gif_name = QLineEdit()
        self.entry_gif_name.setPlaceholderText("nome_do_arquivo")
        self.entry_gif_name.textChanged.connect(lambda _t: self.options_changed.emit())

        lbl_ext = QLabel(".gif")
        lbl_ext.setStyleSheet("color: #a1a1aa; font-weight: bold; font-size: 14px; padding-left: 2px;")

        name_row.addWidget(self.entry_gif_name, stretch=1)
        name_row.addWidget(lbl_ext)

        self.chk_overwrite = QCheckBox("Sobrescrever arquivo se já existir")
        self.chk_overwrite.setChecked(False)

        right_layout.addWidget(lbl_name)
        right_layout.addLayout(name_row)
        right_layout.addWidget(self.chk_overwrite)

        # 4. Parâmetros de Exportação
        grid = QGridLayout()
        grid.setSpacing(10)

        lbl_scale = QLabel("Escala de Tamanho:")
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(list(SCALE_MAP.keys()))
        self.combo_scale.setCurrentIndex(1)  # Padrão: 75%
        self.combo_scale.currentIndexChanged.connect(lambda _idx: self.options_changed.emit())
        grid.addWidget(lbl_scale, 0, 0)
        grid.addWidget(self.combo_scale, 0, 1)

        lbl_skip = QLabel("Intervalo (Skip):")
        self.spin_frame_skip = QSpinBox()
        self.spin_frame_skip.setRange(1, 30)
        self.spin_frame_skip.setValue(5)
        self.spin_frame_skip.setSuffix(" quadros")
        self.spin_frame_skip.valueChanged.connect(lambda _val: self.options_changed.emit())
        grid.addWidget(lbl_skip, 1, 0)
        grid.addWidget(self.spin_frame_skip, 1, 1)

        lbl_speed = QLabel("Velocidade:")
        self.combo_speed = QComboBox()
        self.combo_speed.setEditable(True)
        self.combo_speed.addItems([
            "0.5x",
            "1.0x (Padrão)",
            "1.25x",
            "1.5x",
            "2.0x",
            "3.0x",
            "4.0x",
        ])
        self.combo_speed.setCurrentIndex(1)  # 1.0x (Padrão)
        self.combo_speed.currentTextChanged.connect(lambda _t: self.options_changed.emit())
        grid.addWidget(lbl_speed, 2, 0)
        grid.addWidget(self.combo_speed, 2, 1)

        right_layout.addLayout(grid)

        # Checkbox de paleta de cores mantido aqui
        self.chk_less_colors = QCheckBox("Reduzir paleta de cores (Gera arquivos menores)")
        self.chk_less_colors.setChecked(True)
        self.chk_less_colors.toggled.connect(lambda _checked: self.options_changed.emit())
        right_layout.addWidget(self.chk_less_colors)

        # Espaçador vertical para empurrar o rodapé dinâmico para a base
        right_layout.addStretch(1)

        # 5. Área Inferior Dinâmica (Rodapé do Painel Direito)
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(8)

        self.lbl_size_estimate = QLabel("📊 Estimado: --")
        self.lbl_size_estimate.setObjectName("sizeEstimateLabel")
        self.lbl_size_estimate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_size_estimate.setWordWrap(True)
        footer_layout.addWidget(self.lbl_size_estimate)

        self.lbl_progress_status = QLabel("")
        self.lbl_progress_status.setObjectName("subtitleLabel")
        self.lbl_progress_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_progress_status.setVisible(False)
        footer_layout.addWidget(self.lbl_progress_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        footer_layout.addWidget(self.progress_bar)

        self.lbl_result_status = QLabel("")
        self.lbl_result_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_result_status.setWordWrap(True)
        self.lbl_result_status.setVisible(False)
        footer_layout.addWidget(self.lbl_result_status)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.btn_open_folder = QPushButton("📂 Abrir Pasta")
        self.btn_open_folder.setObjectName("secondaryButton")
        self.btn_open_folder.setFixedHeight(40)
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.setVisible(False)
        self.btn_open_folder.clicked.connect(self.open_folder_requested.emit)

        self.btn_start = QPushButton("🚀 Iniciar Conversão")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.setFixedHeight(40)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_conversion_requested.emit)

        btn_box.addWidget(self.btn_open_folder)
        btn_box.addWidget(self.btn_start)
        footer_layout.addLayout(btn_box)

        right_layout.addLayout(footer_layout)
        main_layout.addWidget(right_card, stretch=37)

        self.set_initial_state()

    def get_selected_scale(self) -> float:
        """Retorna o fator numérico de escala com base na opção selecionada."""
        return SCALE_MAP.get(self.combo_scale.currentText(), 0.75)

    def get_selected_speed(self) -> float:
        """Retorna a velocidade de reprodução numérica validada (> 0.1)."""
        text = self.combo_speed.currentText().strip()
        clean = (
            text.replace("(Padrão)", "")
            .replace("padrão", "")
            .replace("x", "")
            .replace("X", "")
            .strip()
        )
        clean = clean.replace(",", ".")
        try:
            val = float(clean)
            return max(0.1, val)
        except ValueError:
            return 1.0

    def set_size_estimate_text(self, text: str) -> None:
        """Atualiza a mensagem no badge de estimativa e restaura visibilidade padrão."""
        self.lbl_size_estimate.setText(text)
        self.lbl_size_estimate.setVisible(True)
        self.lbl_result_status.setVisible(False)
        self.btn_open_folder.setVisible(False)

    def set_initial_state(self) -> None:
        """Configura o Estado 1 — Inicial (Sem Vídeo Selecionado)."""
        self.entry_input_path.setText("")
        self.entry_output_dir.setText("")
        self.entry_gif_name.setText("")
        self.chk_overwrite.setChecked(False)
        self.combo_speed.setCurrentIndex(1)
        self.lbl_video_meta.setText("")
        self.video_preview.reset()

        self.lbl_size_estimate.setText("📊 Estimado: --")
        self.lbl_size_estimate.setVisible(True)
        self.lbl_progress_status.setVisible(False)
        self.progress_bar.setVisible(False)
        self.lbl_result_status.setVisible(False)
        self.btn_open_folder.setVisible(False)

        self.btn_start.setVisible(True)
        self.btn_start.setEnabled(False)
        self.set_inputs_enabled(False)

    def set_video_loaded_state(self, video_path: Path, output_dir: Path, meta_text: str) -> None:
        """Configura o Estado 2 — Vídeo Carregado (Pronto para Configurar)."""
        self.entry_input_path.setText(str(video_path))
        self.entry_output_dir.setText(str(output_dir))
        self.entry_gif_name.setText(video_path.stem)
        self.lbl_video_meta.setText(meta_text)

        self.set_inputs_enabled(True)
        self.lbl_size_estimate.setVisible(True)
        self.lbl_progress_status.setVisible(False)
        self.progress_bar.setVisible(False)
        self.lbl_result_status.setVisible(False)
        self.btn_open_folder.setVisible(False)

        self.btn_start.setVisible(True)
        self.btn_start.setEnabled(True)

    def set_converting_state(self) -> None:
        """Configura o Estado 3 — Convertendo e Salvando (In-Place Progress)."""
        self.set_inputs_enabled(False)
        self.lbl_size_estimate.setVisible(False)
        self.btn_start.setVisible(False)
        self.btn_open_folder.setVisible(False)
        self.lbl_result_status.setVisible(False)

        self.lbl_progress_status.setVisible(True)
        self.lbl_progress_status.setText("Iniciando conversão...")
        self.lbl_progress_status.setStyleSheet("color: #38bdf8; font-weight: 500;")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

    def set_conversion_completed_state(
        self, success: bool, msg: str = "", is_file_exists: bool = False
    ) -> None:
        """Configura o Estado 4 — Conversão Concluída ou Falha."""
        self.set_inputs_enabled(True)
        self.lbl_progress_status.setVisible(False)
        self.progress_bar.setVisible(False)
        self.lbl_size_estimate.setVisible(False)

        self.btn_start.setVisible(True)
        self.btn_start.setEnabled(True)

        if success:
            self.lbl_result_status.setText("✅ GIF salvo com sucesso!")
            self.lbl_result_status.setStyleSheet(
                "color: #10b981; font-weight: bold; font-size: 13px; padding: 4px;"
            )
            self.lbl_result_status.setVisible(True)
            self.btn_open_folder.setVisible(True)
        else:
            self.lbl_result_status.setText(f"❌ {msg}")
            self.lbl_result_status.setStyleSheet(
                "color: #ef4444; font-weight: bold; font-size: 13px; padding: 4px;"
            )
            self.lbl_result_status.setVisible(True)
            self.btn_open_folder.setVisible(is_file_exists)

    def restore_estimate_display(self) -> None:
        """Restaura a exibição da estimativa caso o status de resultado esteja visível."""
        if self.lbl_result_status.isVisible() or self.btn_open_folder.isVisible():
            self.lbl_result_status.setVisible(False)
            self.btn_open_folder.setVisible(False)
            self.lbl_size_estimate.setVisible(True)

    def set_inputs_enabled(self, enabled: bool) -> None:
        """Controla a habilitação dos campos de configuração durante ou fora da conversão."""
        self.btn_select_file.setEnabled(True)
        self.btn_browse_out.setEnabled(enabled)
        self.entry_gif_name.setEnabled(enabled)
        self.chk_overwrite.setEnabled(enabled)
        self.combo_scale.setEnabled(enabled)
        self.spin_frame_skip.setEnabled(enabled)
        self.combo_speed.setEnabled(enabled)
        self.chk_less_colors.setEnabled(enabled)
        self.video_preview.set_controls_enabled(enabled)
