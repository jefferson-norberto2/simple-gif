import os
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                               QLineEdit, QProgressBar, QStackedWidget, QSpacerItem, 
                               QSizePolicy, QFrame)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from simplegif import SimpleGIF


# ==============================================================================
# 1. CLASSE DO "TRABALHADOR" (THREAD EM SEGUNDO PLANO)
# ==============================================================================
class GifWorker(QThread):
    progress_reading = Signal(float)
    progress_creating = Signal(float)
    finished = Signal()
    error = Signal(str, int) 

    def __init__(self, gif_maker, input_file, output_dir):
        super().__init__()
        self.gif_maker = gif_maker
        self.input_file = input_file
        self.output_dir = output_dir

    def run(self):
        # 1. CRIAMOS OS ADAPTADORES AQUI
        def reading_adapter(current, total):
            if total > 0:
                # Calcula de 0.0 a 1.0 e emite para a interface
                self.progress_reading.emit(current / total)

        def creating_adapter(current, total):
            if total > 0:
                self.progress_creating.emit(current / total)

        try:
            self.gif_maker.convert_file(
                path=self.input_file,
                output_path=self.output_dir,
                scale=0.6,
                less_colors=True,
                max_frames=2000,
                frame_skip=5,
                progress_callback=reading_adapter # 2. PASSAMOS O ADAPTADOR EM VEZ DO EMIT DIRETO
            )
            
            self.gif_maker.save_gif(
                progress_callback=creating_adapter # Aqui também
            )
            
            self.finished.emit()
            
        except Exception as e:
            error_message = str(e.args[0]) if len(e.args) > 0 else "Erro desconhecido"
            error_code = e.args[1] if len(e.args) > 1 else -999
            self.error.emit(error_message, error_code)


# ==============================================================================
# 2. JANELA PRINCIPAL (UI)
# ==============================================================================
class GifConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to GIF")
        self.setFixedSize(500, 350)
        
        # Variáveis de estado
        self.selected_file = None
        self.output_file = None
        self.gif_maker = SimpleGIF()
        
        # Aplicando um estilo global (CSS do Qt) para imitar o CustomTkinter Dark
        self.setStyleSheet("""
            QMainWindow, QWidget#MainContainer { background-color: #242424; }
            QLabel { color: #dce4ee; font-family: 'Roboto', Arial; }
            QPushButton { 
                background-color: #3B8ED0; color: white; 
                border-radius: 15px; padding: 10px; font-weight: bold;
                font-family: 'Roboto', Arial;
            }
            QPushButton:hover { background-color: #36719F; }
            QPushButton#BtnCreate { background-color: #2CC985; }
            QPushButton#BtnCreate:hover { background-color: #229A66; }
            QPushButton#BtnCancel { background-color: transparent; border: 2px solid #565B5E; }
            QPushButton#BtnCancel:hover { background-color: #343638; }
            QLineEdit { 
                background-color: #343638; color: #dce4ee; 
                border: 1px solid #565B5E; border-radius: 5px; padding: 5px; 
            }
            QProgressBar { 
                text-align: center; color: white; border: 1px solid #565B5E; 
                border-radius: 5px; background-color: #343638; height: 20px;
            }
            QProgressBar::chunk { background-color: #2CC985; border-radius: 4px; }
        """)

        # Widget central e Layout Principal
        central_widget = QWidget()
        central_widget.setObjectName("MainContainer")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # O QStackedWidget gerencia nossas "Telas"
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Criando as páginas e adicionando ao Stack
        self.page_initial = self.create_screen_initial()
        self.page_confirm = self.create_screen_confirm()
        self.page_processing = self.create_screen_processing()
        self.page_result = QWidget() # A página de resultado será populada dinamicamente
        
        self.stacked_widget.addWidget(self.page_initial)
        self.stacked_widget.addWidget(self.page_confirm)
        self.stacked_widget.addWidget(self.page_processing)
        self.stacked_widget.addWidget(self.page_result)

        # Começa na primeira tela
        self.stacked_widget.setCurrentWidget(self.page_initial)

    # --- TELA 1: Inicial ---
    def create_screen_initial(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centraliza tudo

        lbl_title = QLabel("Conversor de GIF")
        lbl_title.setFont(QFont("Roboto", 20, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        layout.addSpacing(20)

        btn_file = QPushButton("Escolher Arquivo de Vídeo")
        btn_file.setFixedSize(200, 50)
        btn_file.clicked.connect(self.select_file) # Conecta o clique à função
        layout.addWidget(btn_file, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return page

    def select_file(self):
        # Abre a janela de seleção do sistema
        filename, _ = QFileDialog.getOpenFileName(
            self, "Selecione o Vídeo", "", "Arquivos de Vídeo (*.mp4 *.avi *.mov *.mkv)"
        )
        if filename:
            self.selected_file = filename
            base, _ = os.path.splitext(filename)
            self.output_file = f"{base}.gif"
            
            # Atualiza o campo de texto da próxima tela com o caminho
            self.entry_path.setText(self.selected_file)
            # Muda para a tela de confirmação
            self.stacked_widget.setCurrentWidget(self.page_confirm)

    # --- TELA 2: Confirmação ---
    def create_screen_confirm(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        layout.addStretch() # Empurra tudo para baixo

        lbl_info = QLabel("Arquivo Selecionado:")
        lbl_info.setFont(QFont("Roboto", 12))
        layout.addWidget(lbl_info)

        self.entry_path = QLineEdit()
        self.entry_path.setReadOnly(True)
        layout.addWidget(self.entry_path)
        
        layout.addSpacing(30)

        # Layout Horizontal para os botões lado a lado
        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("BtnCancel")
        btn_cancel.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.page_initial))
        btn_layout.addWidget(btn_cancel)

        btn_create = QPushButton("Criar GIF")
        btn_create.setObjectName("BtnCreate")
        btn_create.clicked.connect(self.start_processing)
        btn_layout.addWidget(btn_create)

        layout.addLayout(btn_layout)
        layout.addStretch() # Empurra tudo para cima (deixando no centro)

        return page

    # --- TELA 3: Processando ---
    def create_screen_processing(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_process = QLabel("Processando seu GIF...")
        self.lbl_process.setFont(QFont("Roboto", 16, QFont.Weight.Bold))
        self.lbl_process.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_process)
        
        layout.addSpacing(20)

        self.lbl_step = QLabel("Passo 1/3: Lendo Arquivo")
        self.lbl_step.setStyleSheet("color: #2CC985;")
        self.lbl_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_step)

        self.progressbar = QProgressBar()
        self.progressbar.setRange(0, 100) # De 0 a 100%
        self.progressbar.setValue(0)
        self.progressbar.setFixedWidth(300)
        layout.addWidget(self.progressbar, alignment=Qt.AlignmentFlag.AlignCenter)

        return page

    # --- LÓGICA DE PROCESSAMENTO (SINAIS E SLOTS) ---
    def start_processing(self):
        # Reset visual
        self.progressbar.setValue(0)
        self.lbl_step.setText("Passo 1/3: Lendo Arquivo")
        self.stacked_widget.setCurrentWidget(self.page_processing)

        output_dir = os.path.dirname(self.output_file)
        if not output_dir:
            output_dir = "."

        # Cria a thread passando as informações
        self.worker = GifWorker(self.gif_maker, self.selected_file, output_dir)
        
        # Conecta os sinais que a Thread emite às funções da nossa tela
        self.worker.progress_reading.connect(self._update_ui_reading)
        self.worker.progress_creating.connect(self._update_ui_creating)
        self.worker.finished.connect(lambda: self.setup_screen_result(False))
        self.worker.error.connect(lambda msg, code: self.setup_screen_result(True, msg, code))
        
        # Inicia a thread
        self.worker.start()

    def _update_ui_reading(self, progress):
        self.lbl_step.setText("Passo 1/3: Lendo Arquivo")
        self.progressbar.setValue(int(progress * 100))

    def _update_ui_creating(self, progress):
        self.lbl_step.setText("Passo 2/3: Criando GIF")
        percentage = int(progress * 100)
        self.progressbar.setValue(percentage)
        
        if percentage >= 100:
            self.lbl_step.setText("Passo 3/3: Salvando no Disco")

    # --- TELA 4: Resultado Dinâmico ---
    def setup_screen_result(self, have_error=False, error_message="", error_code=0):
        # Limpa o que tinha na tela de resultado (similar ao seu clear_frame, mas apenas para esta página)
        if self.page_result.layout():
            QWidget().setLayout(self.page_result.layout()) 
            
        layout = QVBoxLayout(self.page_result)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if have_error:
            lbl_status = QLabel("Erro durante a conversão!")
            lbl_status.setFont(QFont("Roboto", 18, QFont.Weight.Bold))
            lbl_status.setStyleSheet("color: #FF5555;") # Vermelho para erro
            layout.addWidget(lbl_status, alignment=Qt.AlignmentFlag.AlignCenter)
            
            lbl_msg = QLabel(error_message)
            layout.addWidget(lbl_msg, alignment=Qt.AlignmentFlag.AlignCenter)
            
            layout.addSpacing(20)

            if error_code in [-1, -2]:
                btn_open = QPushButton("📁 Abrir Pasta de Destino")
                btn_open.setFixedWidth(200)
                btn_open.clicked.connect(self.open_output_folder)
                layout.addWidget(btn_open, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            lbl_status = QLabel("Concluído!")
            lbl_status.setFont(QFont("Roboto", 18, QFont.Weight.Bold))
            lbl_status.setStyleSheet("color: #2CC985;")
            layout.addWidget(lbl_status, alignment=Qt.AlignmentFlag.AlignCenter)
            
            lbl_info = QLabel("Arquivo salvo em:")
            layout.addWidget(lbl_info, alignment=Qt.AlignmentFlag.AlignCenter)
            
            # Container horizontal para o campo de texto e botão
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(30, 0, 30, 0)
            
            entry_out = QLineEdit(self.output_file)
            entry_out.setReadOnly(True)
            h_layout.addWidget(entry_out)
            
            btn_folder = QPushButton("📁")
            btn_folder.setFixedSize(40, 40) # Botão quadrado para o ícone
            btn_folder.clicked.connect(self.open_output_folder)
            h_layout.addWidget(btn_folder)
            
            layout.addLayout(h_layout)

        layout.addSpacing(30)
        btn_ok = QPushButton("Novo Arquivo")
        btn_ok.setFixedWidth(150)
        btn_ok.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.page_initial))
        layout.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignCenter)

        # Mostra a página
        self.stacked_widget.setCurrentWidget(self.page_result)

    def open_output_folder(self):
        folder_path = os.path.dirname(os.path.abspath(self.output_file))
        # O QDesktopServices substitui o 'os.startfile', 'subprocess' e 'open' de uma vez só!
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GifConverterApp()
    window.show()
    sys.exit(app.exec())