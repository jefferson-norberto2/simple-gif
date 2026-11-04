"""Tela de progresso do processamento de vídeo para GIF."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget


class ProcessingScreen(QWidget):
    """Tela com duas barras de progresso informando leitura e gravação em tempo real."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
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

        # Passo 1/2: Leitura e Preparação
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

        # Passo 2/2: Codificação e Gravação
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

    def reset_progress(self) -> None:
        """Reinicia os indicadores para novo processamento."""
        self.read_progress_bar.setValue(0)
        self.save_progress_bar.setValue(0)
        self.lbl_read_status.setText("Iniciando leitura do trecho selecionado...")
        self.lbl_read_status.setStyleSheet("color: #a1a1aa;")
        self.lbl_save_status.setText("Aguardando preparação dos frames...")
        self.lbl_save_status.setStyleSheet("color: #71717a;")

    def update_read_progress(self, current: int, total: int) -> None:
        """Atualiza a barra e o texto da etapa 1 (leitura de frames)."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.read_progress_bar.setValue(percentage)
            if percentage >= 100:
                self.lbl_read_status.setText(f"✓ Todos os {total} frames do trecho foram lidos e preparados!")
                self.lbl_read_status.setStyleSheet("color: #10b981; font-weight: 500;")
                self.lbl_save_status.setText("Iniciando codificação e gravação no disco...")
                self.lbl_save_status.setStyleSheet("color: #38bdf8;")
            else:
                self.lbl_read_status.setText(f"Lendo e redimensionando: {current}/{total} frames ({percentage}%)")
                self.lbl_read_status.setStyleSheet("color: #a1a1aa;")

    def update_save_progress(self, current: int, total: int) -> None:
        """Atualiza a barra e o texto da etapa 2 (gravação do GIF)."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.save_progress_bar.setValue(percentage)
            if percentage >= 100:
                self.lbl_save_status.setText("✓ GIF codificado e gravado no disco com sucesso!")
                self.lbl_save_status.setStyleSheet("color: #10b981; font-weight: 500;")
            else:
                self.lbl_save_status.setText(f"Codificando e gravando frame {current}/{total} ({percentage}%)...")
                self.lbl_save_status.setStyleSheet("color: #38bdf8;")
