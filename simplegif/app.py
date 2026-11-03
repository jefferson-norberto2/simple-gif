"""Interface gráfica CustomTkinter para o conversor SimpleGIF."""

import os
from pathlib import Path
import platform
import subprocess
import threading
from tkinter import filedialog

import customtkinter as ctk

try:
    from simplegif.simplegif import SimpleGIF
except ImportError:
    from simplegif import SimpleGIF  # type: ignore[no-redef]


class GifConverterApp:
    """Aplicação CustomTkinter para converter vídeos em GIFs com interface amigável."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Video to GIF")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        # Variáveis de estado
        self.selected_file: Path | None = None
        self.output_file: Path | None = None

        self.gif_maker = SimpleGIF()

        # Container principal
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=15)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.error_message: str = ""
        self.is_file_exists_error: bool = False

        # Inicia na primeira tela
        self.show_screen_initial()

        self.root.mainloop()

    def clear_frame(self) -> None:
        """Limpa os widgets do frame principal."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # --- TELA 1: Inicial ---
    def show_screen_initial(self) -> None:
        """Exibe a tela inicial para seleção do arquivo de vídeo."""
        self.clear_frame()

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)

        lbl_title = ctk.CTkLabel(self.main_frame, text="Conversor de GIF", font=("Roboto Medium", 24))
        lbl_title.grid(row=1, column=0, pady=(0, 20))

        btn_file = ctk.CTkButton(
            self.main_frame,
            text="Escolher Arquivo de Vídeo",
            command=self.select_file,
            width=200,
            height=50,
            font=("Roboto", 14),
            corner_radius=25,
        )
        btn_file.grid(row=2, column=0)

    def select_file(self) -> None:
        """Abre caixa de diálogo para seleção do vídeo e define caminhos com pathlib.Path."""
        filename = filedialog.askopenfilename(
            title="Selecione o Vídeo",
            filetypes=[("Arquivos de Vídeo", "*.mp4 *.avi *.mov *.mkv")],
        )
        if filename:
            self.selected_file = Path(filename).resolve()
            self.output_file = self.selected_file.with_suffix(".gif")
            self.show_screen_confirm()

    # --- TELA 2: Confirmação ---
    def show_screen_confirm(self) -> None:
        """Exibe os dados do arquivo selecionado e botões de ação."""
        self.clear_frame()
        self.main_frame.grid_columnconfigure(0, weight=1)

        lbl_info = ctk.CTkLabel(self.main_frame, text="Arquivo Selecionado:", font=("Roboto", 14), anchor="w")
        lbl_info.pack(fill="x", padx=20, pady=(30, 5))

        entry_path = ctk.CTkEntry(self.main_frame, placeholder_text=str(self.selected_file))
        entry_path.insert(0, str(self.selected_file))
        entry_path.configure(state="disabled")
        entry_path.pack(fill="x", padx=20, pady=(0, 30))

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE"),
            command=self.show_screen_initial,
        )
        btn_cancel.pack(side="left", expand=True, fill="x", padx=(0, 10))

        btn_create = ctk.CTkButton(
            btn_frame,
            text="Criar GIF",
            fg_color="#2CC985",
            hover_color="#229A66",
            text_color="white",
            command=self.start_processing,
        )
        btn_create.pack(side="right", expand=True, fill="x", padx=(10, 0))

    # --- TELA 3: Processando ---
    def show_screen_processing(self) -> None:
        """Exibe a tela de processamento com barra de progresso."""
        self.clear_frame()

        lbl_process = ctk.CTkLabel(self.main_frame, text="Processando seu GIF...", font=("Roboto Medium", 18))
        lbl_process.pack(pady=(40, 20))

        self.lbl_step = ctk.CTkLabel(
            self.main_frame,
            text="Iniciando conversão...",
            font=("Roboto", 12),
            text_color="#2CC985",
        )
        self.lbl_step.pack(pady=(0, 5))

        self.progressbar = ctk.CTkProgressBar(self.main_frame, width=300)
        self.progressbar.pack(pady=10)
        self.progressbar.set(0.0)

    def update_progress(self, current_frame: int, total_frames: int) -> None:
        """Atualiza o estado de progresso de forma thread-safe na UI."""
        if total_frames > 0:
            progress = min(1.0, current_frame / total_frames)
            self.root.after(0, self._update_ui_progress, progress, current_frame, total_frames)

    def _update_ui_progress(self, progress: float, current_frame: int, total_frames: int) -> None:
        percentage = int(progress * 100)
        if percentage >= 100:
            self.lbl_step.configure(text="Finalizando gravação do GIF no disco...")
        else:
            self.lbl_step.configure(text=f"Processando frames: {current_frame}/{total_frames} ({percentage}%)")
        self.progressbar.set(progress)

    def update_progress_saving(self, current_frame: int, total_frames: int) -> None:
        """Compatibilidade para atualizações de progresso."""
        self.update_progress(current_frame, total_frames)

    def start_processing(self) -> None:
        """Inicia a thread em segundo plano para conversão assíncrona."""
        self.show_screen_processing()
        threading.Thread(target=self.conversion_logic, daemon=True).start()

    def conversion_logic(self) -> None:
        """Executa a conversão via streaming e trata exceções semanticamente."""
        if self.selected_file is None:
            self.error_message = "Nenhum arquivo de vídeo foi selecionado."
            self.is_file_exists_error = False
            self.root.after(0, self.show_screen_result, True)
            return

        output_dir = self.output_file.parent if self.output_file else self.selected_file.parent

        try:
            generated_path = self.gif_maker.convert_file(
                path=self.selected_file,
                output_path=output_dir,
                scale=0.6,
                less_colors=True,
                max_frames=2000,
                frame_skip=5,
                progress_callback=self.update_progress,
            )
            self.output_file = generated_path
            self.root.after(0, self.show_screen_result, False)
        except FileExistsError as e:
            self.error_message = str(e)
            self.is_file_exists_error = True
            self.root.after(0, self.show_screen_result, True)
        except FileNotFoundError as e:
            self.error_message = str(e)
            self.is_file_exists_error = False
            self.root.after(0, self.show_screen_result, True)
        except Exception as e:
            self.error_message = f"Erro inesperado: {e}"
            self.is_file_exists_error = False
            self.root.after(0, self.show_screen_result, True)

    # --- TELA 4: Resultado ---
    def show_screen_result(self, have_error: bool = False) -> None:
        """Exibe o resultado da conversão com opção de abrir pasta ou mensagem de erro."""
        self.clear_frame()

        if have_error:
            lbl_title = ctk.CTkLabel(
                self.main_frame,
                text="Erro durante a conversão!",
                font=("Roboto Medium", 20),
                text_color="#FF4C4C",
            )
            lbl_title.pack(pady=(30, 10))

            lbl_info = ctk.CTkLabel(
                self.main_frame,
                text=self.error_message,
                font=("Roboto", 12),
                wraplength=420,
            )
            lbl_info.pack(pady=(5, 10))

            if self.is_file_exists_error:
                btn_open_folder = ctk.CTkButton(
                    self.main_frame,
                    text="📁 Abrir Pasta de Destino",
                    command=self.open_output_folder,
                    fg_color="#3B8ED0",
                    hover_color="#36719F",
                )
                btn_open_folder.pack(pady=10)
        else:
            lbl_success = ctk.CTkLabel(
                self.main_frame,
                text="Concluído!",
                font=("Roboto Medium", 22),
                text_color="#2CC985",
            )
            lbl_success.pack(pady=(40, 10))

            lbl_info = ctk.CTkLabel(self.main_frame, text="Arquivo salvo em:", font=("Roboto", 12))
            lbl_info.pack(pady=(10, 5))

            result_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            result_frame.pack(fill="x", padx=30, pady=10)
            result_frame.grid_columnconfigure(0, weight=1)

            entry_out = ctk.CTkEntry(result_frame, justify="left")
            entry_out.insert(0, str(self.output_file) if self.output_file else "")
            entry_out.configure(state="readonly")
            entry_out.grid(row=0, column=0, sticky="ew", padx=(0, 10))

            btn_open_folder = ctk.CTkButton(
                result_frame,
                text="📁",
                width=40,
                command=self.open_output_folder,
                fg_color="#3B8ED0",
                hover_color="#36719F",
            )
            btn_open_folder.grid(row=0, column=1)

        btn_ok = ctk.CTkButton(
            self.main_frame,
            text="Novo Arquivo",
            command=self.show_screen_initial,
            width=150,
        )
        btn_ok.pack(pady=25)

    def open_output_folder(self) -> None:
        """Abre o gerenciador de arquivos na pasta de destino de forma segura."""
        if not self.output_file:
            return

        target_path = Path(self.output_file).resolve()
        folder_path = target_path if target_path.is_dir() else target_path.parent

        if not folder_path.is_dir():
            return

        current_os = platform.system()
        if current_os == "Windows":
            os.startfile(folder_path)
        elif current_os == "Darwin":  # macOS
            subprocess.Popen(["open", str(folder_path)])
        else:  # Linux / POSIX
            subprocess.Popen(["xdg-open", str(folder_path)])


if __name__ == "__main__":
    app = GifConverterApp()
