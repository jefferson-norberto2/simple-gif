"""Interface gráfica para conversão de vídeos em GIF utilizando PySide6 (Qt)."""

from pathlib import Path
import sys

from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from simplegif import SimpleGIF


def load_stylesheet(qss_name: str = "style.qss") -> str:
    """Carrega as folhas de estilo QSS a partir de arquivo externo (compatível com PyInstaller)."""
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
        qss_file = base_dir / "simplegif" / qss_name
        if not qss_file.is_file():
            qss_file = base_dir / qss_name
    else:
        qss_file = Path(__file__).resolve().parent / qss_name

    if qss_file.is_file():
        return qss_file.read_text(encoding="utf-8")
    return ""


class ConversionWorker(QThread):
    """Worker que executa a conversão do vídeo para GIF em segundo plano via QThread."""

    read_progress_updated = Signal(int, int)  # (atual, total)
    save_progress_updated = Signal(int, int)  # (atual, total)
    conversion_completed = Signal(Path)
    conversion_failed = Signal(str, bool)     # (mensagem_erro, eh_file_exists)

    def __init__(
        self,
        gif_maker: SimpleGIF,
        input_path: Path,
        output_path: Path,
        scale: float,
        frame_skip: int,
        less_colors: bool,
        overwrite: bool,
    ) -> None:
        super().__init__()
        self.gif_maker = gif_maker
        self.input_path = input_path
        self.output_path = output_path
        self.scale = scale
        self.frame_skip = frame_skip
        self.less_colors = less_colors
        self.overwrite = overwrite

    def run(self) -> None:
        """Executa a conversão com callbacks reportados por Signals."""
        try:
            result_path = self.gif_maker.convert_file(
                path=self.input_path,
                output_path=self.output_path,
                scale=self.scale,
                less_colors=self.less_colors,
                max_frames=3000,
                frame_skip=self.frame_skip,
                overwrite=self.overwrite,
                read_progress_callback=self._on_read_progress,
                save_progress_callback=self._on_save_progress,
            )
            self.conversion_completed.emit(result_path)
        except FileExistsError as e:
            self.conversion_failed.emit(str(e), True)
        except Exception as e:
            self.conversion_failed.emit(str(e), False)

    def _on_read_progress(self, current: int, total: int) -> None:
        self.read_progress_updated.emit(current, total)

    def _on_save_progress(self, current: int, total: int) -> None:
        self.save_progress_updated.emit(current, total)


class GifConverterApp(QMainWindow):
    """Janela principal da aplicação Simple GIF Maker desenvolvida com PySide6."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Simple GIF Maker")
        self.setFixedSize(580, 530)
        self.setStyleSheet(load_stylesheet())

        self.gif_maker = SimpleGIF()
        self.selected_file: Path | None = None
        self.output_dir: Path | None = None
        self.result_gif_path: Path | None = None
        self.worker: ConversionWorker | None = None

        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        self.screen_initial = self._create_screen_initial()
        self.screen_options = self._create_screen_options()
        self.screen_processing = self._create_screen_processing()
        self.screen_result = self._create_screen_result()

        self.stacked_widget.addWidget(self.screen_initial)     # Index 0
        self.stacked_widget.addWidget(self.screen_options)     # Index 1
        self.stacked_widget.addWidget(self.screen_processing)  # Index 2
        self.stacked_widget.addWidget(self.screen_result)      # Index 3

        self.show_screen_initial()

    # --- TELA 1: Seleção Inicial ---
    def _create_screen_initial(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
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

        btn_select = QPushButton(" Escolher Arquivo de Vídeo")
        btn_select.setObjectName("primaryButton")
        btn_select.setFixedHeight(48)
        btn_select.setFixedWidth(240)
        btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select.clicked.connect(self.select_file)

        lbl_formats = QLabel("Formatos suportados: MP4, AVI, MOV, MKV")
        lbl_formats.setObjectName("subtitleLabel")
        lbl_formats.setStyleSheet("font-size: 11px; color: #71717a;")
        lbl_formats.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(lbl_icon)
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_sub)
        card_layout.addSpacing(10)
        card_layout.addWidget(btn_select, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_formats)

        layout.addWidget(card)
        return widget

    def select_file(self) -> None:
        """Abre o diálogo nativo do SO para escolher o arquivo de vídeo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o Vídeo",
            "",
            "Arquivos de Vídeo (*.mp4 *.avi *.mov *.mkv);;Todos os Arquivos (*.*)",
        )
        if file_path:
            self.selected_file = Path(file_path).resolve()
            self.output_dir = self.selected_file.parent
            self.update_options_screen()
            self.stacked_widget.setCurrentIndex(1)

    # --- TELA 2: Configuração e Confirmação ---
    def _create_screen_options(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 18, 25, 18)
        card_layout.setSpacing(13)

        lbl_title = QLabel("Configurar Conversão")
        lbl_title.setObjectName("sectionTitle")
        card_layout.addWidget(lbl_title)

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
        btn_browse_out = QPushButton("Alterar...")
        btn_browse_out.clicked.connect(self.browse_output_dir)
        out_row.addWidget(self.entry_output_dir)
        out_row.addWidget(btn_browse_out)
        card_layout.addLayout(out_row)

        # Grade de Opções
        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Escala de Tamanho:"), 0, 0)
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(["100% (Original)", "75%", "60% (Recomendado)", "50%", "35%", "25%"])
        self.combo_scale.setCurrentIndex(2)  # 60%
        grid.addWidget(self.combo_scale, 0, 1)

        grid.addWidget(QLabel("Intervalo de Quadros (Skip):"), 1, 0)
        self.spin_frame_skip = QSpinBox()
        self.spin_frame_skip.setRange(1, 30)
        self.spin_frame_skip.setValue(5)
        self.spin_frame_skip.setSuffix(" quadros")
        grid.addWidget(self.spin_frame_skip, 1, 1)

        card_layout.addLayout(grid)

        # Checkboxes
        self.chk_less_colors = QCheckBox("Reduzir paleta de cores (Gera arquivos menores)")
        self.chk_less_colors.setChecked(True)
        card_layout.addWidget(self.chk_less_colors)

        self.chk_overwrite = QCheckBox("Sobrescrever arquivo se já existir")
        self.chk_overwrite.setChecked(False)
        card_layout.addWidget(self.chk_overwrite)

        layout.addWidget(card)

        # Botões de Ação
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Voltar")
        btn_cancel.setObjectName("secondaryButton")
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.show_screen_initial)

        btn_start = QPushButton("🚀 Iniciar Conversão")
        btn_start.setObjectName("primaryButton")
        btn_start.setFixedHeight(40)
        btn_start.clicked.connect(self.start_conversion)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_start)
        layout.addLayout(btn_box)

        return widget

    def update_options_screen(self) -> None:
        """Atualiza os campos da tela de opções com base no arquivo selecionado."""
        if self.selected_file:
            self.entry_input_path.setText(str(self.selected_file))
        if self.output_dir:
            self.entry_output_dir.setText(str(self.output_dir))

    def browse_output_dir(self) -> None:
        """Permite ao usuário escolher outra pasta de destino."""
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Selecione a Pasta de Destino",
            str(self.output_dir or Path.home()),
        )
        if selected_dir:
            self.output_dir = Path(selected_dir).resolve()
            self.entry_output_dir.setText(str(self.output_dir))

    # --- TELA 3: Processamento com Duas Barras de Progresso ---
    def _create_screen_processing(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(35, 30, 35, 30)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(14)

        lbl_title = QLabel("Processando seu GIF...")
        lbl_title.setObjectName("titleLabel")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_title)

        # --- ETAPA 1: Leitura e Processamento ---
        card_layout.addSpacing(6)
        lbl_step1 = QLabel("Passo 1/2: Leitura e Preparação dos Quadros")
        lbl_step1.setObjectName("sectionTitle")
        card_layout.addWidget(lbl_step1)

        self.lbl_read_status = QLabel("Aguardando início...")
        self.lbl_read_status.setObjectName("subtitleLabel")
        card_layout.addWidget(self.lbl_read_status)

        self.read_progress_bar = QProgressBar()
        self.read_progress_bar.setRange(0, 100)
        self.read_progress_bar.setValue(0)
        card_layout.addWidget(self.read_progress_bar)

        # --- ETAPA 2: Gravação e Codificação do GIF ---
        card_layout.addSpacing(10)
        lbl_step2 = QLabel("Passo 2/2: Codificação e Gravação do GIF")
        lbl_step2.setObjectName("sectionTitle")
        card_layout.addWidget(lbl_step2)

        self.lbl_save_status = QLabel("Aguardando leitura dos frames...")
        self.lbl_save_status.setObjectName("subtitleLabel")
        card_layout.addWidget(self.lbl_save_status)

        self.save_progress_bar = QProgressBar()
        self.save_progress_bar.setRange(0, 100)
        self.save_progress_bar.setValue(0)
        card_layout.addWidget(self.save_progress_bar)

        layout.addWidget(card)
        return widget

    def start_conversion(self) -> None:
        """Coleta as opções e dispara o QThread de processamento."""
        if not self.selected_file or not self.output_dir:
            return

        scale_map = {
            "100% (Original)": 1.0,
            "75%": 0.75,
            "60% (Recomendado)": 0.6,
            "50%": 0.5,
            "35%": 0.35,
            "25%": 0.25,
        }
        chosen_scale = scale_map.get(self.combo_scale.currentText(), 0.6)
        frame_skip = self.spin_frame_skip.value()
        less_colors = self.chk_less_colors.isChecked()
        overwrite = self.chk_overwrite.isChecked()

        self.read_progress_bar.setValue(0)
        self.save_progress_bar.setValue(0)
        self.lbl_read_status.setText("Iniciando leitura do arquivo de vídeo...")
        self.lbl_read_status.setStyleSheet("color: #a1a1aa;")
        self.lbl_save_status.setText("Aguardando preparação dos frames...")
        self.lbl_save_status.setStyleSheet("color: #71717a;")
        self.stacked_widget.setCurrentIndex(2)

        self.worker = ConversionWorker(
            gif_maker=self.gif_maker,
            input_path=self.selected_file,
            output_path=self.output_dir,
            scale=chosen_scale,
            frame_skip=frame_skip,
            less_colors=less_colors,
            overwrite=overwrite,
        )
        self.worker.read_progress_updated.connect(self.on_read_progress_update)
        self.worker.save_progress_updated.connect(self.on_save_progress_update)
        self.worker.conversion_completed.connect(self.on_conversion_completed)
        self.worker.conversion_failed.connect(self.on_conversion_failed)
        self.worker.start()

    def on_read_progress_update(self, current: int, total: int) -> None:
        """Slot para atualização em tempo real da barra de leitura dos frames."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.read_progress_bar.setValue(percentage)
            if percentage >= 100:
                self.lbl_read_status.setText(f"✓ Todos os {total} frames foram lidos e preparados!")
                self.lbl_read_status.setStyleSheet("color: #10b981; font-weight: 500;")
                self.lbl_save_status.setText("Iniciando codificação e gravação no disco...")
                self.lbl_save_status.setStyleSheet("color: #38bdf8;")
            else:
                self.lbl_read_status.setText(f"Lendo e redimensionando: {current}/{total} frames ({percentage}%)")
                self.lbl_read_status.setStyleSheet("color: #a1a1aa;")

    def on_save_progress_update(self, current: int, total: int) -> None:
        """Slot para atualização em tempo real da barra de gravação do GIF."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.save_progress_bar.setValue(percentage)
            if percentage >= 100:
                self.lbl_save_status.setText("✓ GIF codificado e gravado no disco com sucesso!")
                self.lbl_save_status.setStyleSheet("color: #10b981; font-weight: 500;")
            else:
                self.lbl_save_status.setText(f"Codificando e gravando frame {current}/{total} ({percentage}%)...")
                self.lbl_save_status.setStyleSheet("color: #38bdf8;")

    def on_conversion_completed(self, gif_path: Path) -> None:
        """Slot acionado quando a conversão for concluída com sucesso."""
        self.result_gif_path = gif_path
        self.show_screen_result(success=True)

    def on_conversion_failed(self, error_message: str, is_file_exists: bool) -> None:
        """Slot acionado em caso de erro na conversão."""
        self.result_gif_path = None
        self.show_screen_result(success=False, error_msg=error_message, is_file_exists=is_file_exists)

    # --- TELA 4: Resultado ---
    def _create_screen_result(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(35, 30, 35, 30)

        card = QFrame()
        card.setObjectName("cardFrame")
        self.card_result_layout = QVBoxLayout(card)
        self.card_result_layout.setContentsMargins(30, 30, 30, 30)
        self.card_result_layout.setSpacing(16)
        self.card_result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        btn_copy = QPushButton("Copiar")
        btn_copy.clicked.connect(self.copy_path_to_clipboard)
        self.path_box.addWidget(self.entry_res_path)
        self.path_box.addWidget(btn_copy)

        self.btn_open_folder = QPushButton("📁 Abrir Pasta de Destino")
        self.btn_open_folder.clicked.connect(self.open_destination_folder)
        self.btn_open_folder.setFixedHeight(38)

        self.btn_new_file = QPushButton("Converter Novo Vídeo")
        self.btn_new_file.setObjectName("primaryButton")
        self.btn_new_file.setFixedHeight(42)
        self.btn_new_file.setFixedWidth(200)
        self.btn_new_file.clicked.connect(self.show_screen_initial)

        self.card_result_layout.addWidget(self.lbl_res_icon)
        self.card_result_layout.addWidget(self.lbl_res_title)
        self.card_result_layout.addWidget(self.lbl_res_desc)
        self.card_result_layout.addLayout(self.path_box)
        self.card_result_layout.addWidget(self.btn_open_folder, alignment=Qt.AlignmentFlag.AlignCenter)
        self.card_result_layout.addSpacing(10)
        self.card_result_layout.addWidget(self.btn_new_file, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card)
        return widget

    def show_screen_result(
        self,
        success: bool,
        error_msg: str = "",
        is_file_exists: bool = False,
    ) -> None:
        """Configura e exibe a tela de resultado dependendo do status de sucesso ou erro."""
        if success:
            self.lbl_res_icon.setText("✅")
            self.lbl_res_title.setText("GIF Gerado com Sucesso!")
            self.lbl_res_title.setStyleSheet("color: #10b981; font-size: 20px; font-weight: bold;")
            self.lbl_res_desc.setText("Arquivo disponível em:")
            self.entry_res_path.setVisible(True)
            self.entry_res_path.setText(str(self.result_gif_path))
            self.btn_open_folder.setVisible(True)
        else:
            self.lbl_res_icon.setText("❌")
            self.lbl_res_title.setText("Falha na Conversão")
            self.lbl_res_title.setStyleSheet("color: #ef4444; font-size: 20px; font-weight: bold;")
            self.lbl_res_desc.setText(error_msg)
            self.entry_res_path.setVisible(False)
            self.btn_open_folder.setVisible(is_file_exists)

        self.stacked_widget.setCurrentIndex(3)

    def copy_path_to_clipboard(self) -> None:
        """Copia o caminho do GIF gerado para a área de transferência."""
        if self.result_gif_path:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(str(self.result_gif_path))

    def open_destination_folder(self) -> None:
        """Abre a pasta de destino de forma segura e nativa usando QDesktopServices."""
        target_dir = self.output_dir
        if self.result_gif_path and self.result_gif_path.parent.is_dir():
            target_dir = self.result_gif_path.parent

        if target_dir and target_dir.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target_dir)))

    def show_screen_initial(self) -> None:
        """Retorna para a tela inicial de seleção."""
        self.selected_file = None
        self.result_gif_path = None
        self.stacked_widget.setCurrentIndex(0)


def main() -> None:
    """Função de entrada para inicialização da interface gráfica PySide6."""
    app = QApplication(sys.argv)
    window = GifConverterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
