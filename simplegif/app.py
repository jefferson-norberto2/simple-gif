import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import subprocess
import platform
from simplegif import SimpleGIF


class GifConverterApp:
    def __init__(self):
        # Configurações globais do tema
        ctk.set_appearance_mode("Dark")  # Modos: "System" (padrão), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Temas: "blue" (padrão), "green", "dark-blue"

        self.root = ctk.CTk()  # Usamos CTk em vez de Tk
        self.root.title("Video to GIF")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Variáveis de estado
        self.selected_file = None
        self.output_file = None
        
        self.gif_maker = SimpleGIF()
        
        # Container principal
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=15)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.error_message = ""
        self.error_code = 0
        
        # Inicia na primeira tela
        self.show_screen_initial()

        self.root.mainloop()

    def clear_frame(self):
        """Limpa os widgets do frame principal"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # --- TELA 1: Inicial ---
    def show_screen_initial(self):
        self.clear_frame()
        
        # Centralizar conteúdo
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1) # Espaço antes
        self.main_frame.grid_rowconfigure(3, weight=1) # Espaço depois

        lbl_title = ctk.CTkLabel(self.main_frame, text="Conversor de GIF", font=("Roboto Medium", 24))
        lbl_title.grid(row=1, column=0, pady=(0, 20))

        btn_file = ctk.CTkButton(
            self.main_frame, 
            text="Escolher Arquivo de Vídeo", 
            command=self.select_file,
            width=200,
            height=50,
            font=("Roboto", 14),
            corner_radius=25
        )
        btn_file.grid(row=2, column=0)

    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Selecione o Vídeo",
            filetypes=[("Arquivos de Vídeo", "*.mp4 *.avi *.mov *.mkv")]
        )
        if filename:
            self.selected_file = filename
            base, _ = os.path.splitext(filename)
            self.output_file = f"{base}.gif"
            self.show_screen_confirm()

    # --- TELA 2: Confirmação ---
    def show_screen_confirm(self):
        self.clear_frame()
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Título
        lbl_info = ctk.CTkLabel(self.main_frame, text="Arquivo Selecionado:", font=("Roboto", 14), anchor="w")
        lbl_info.pack(fill="x", padx=20, pady=(30, 5))
        
        # Mostra o caminho (com fundo mais escuro)
        entry_path = ctk.CTkEntry(self.main_frame, placeholder_text=self.selected_file)
        entry_path.insert(0, self.selected_file)
        entry_path.configure(state="disabled") # Apenas leitura
        entry_path.pack(fill="x", padx=20, pady=(0, 30))
        
        # Botões lado a lado
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)
        
        btn_cancel = ctk.CTkButton(
            btn_frame, 
            text="Cancelar", 
            fg_color="transparent", 
            border_width=2, 
            text_color=("gray10", "#DCE4EE"), 
            command=self.show_screen_initial
        )
        btn_cancel.pack(side="left", expand=True, fill="x", padx=(0, 10))

        btn_create = ctk.CTkButton(
            btn_frame, 
            text="Criar GIF", 
            fg_color="#2CC985", # Um verde bonito
            hover_color="#229A66",
            text_color="white",
            command=self.start_processing
        )
        btn_create.pack(side="right", expand=True, fill="x", padx=(10, 0))

    # --- TELA 3: Processando (Com Barra de Progresso e Passos) ---
    def show_screen_processing(self):
        self.clear_frame()
        
        lbl_process = ctk.CTkLabel(self.main_frame, text="Processando seu GIF...", font=("Roboto Medium", 18))
        lbl_process.pack(pady=(40, 20))
        
        # --- LABEL PARA OS PASSOS ---
        self.lbl_step = ctk.CTkLabel(self.main_frame, text="Passo 1/3: Lendo Arquivo", font=("Roboto", 12), text_color="#2CC985")
        self.lbl_step.pack(pady=(0, 5))
        
        # REMOVA o modo "indeterminate" e inicie a barra no zero
        self.progressbar = ctk.CTkProgressBar(self.main_frame, width=300)
        self.progressbar.pack(pady=10)
        self.progressbar.set(0.0) # Inicia vazia (modo determinate é o padrão)
    
    # --- NOVA FUNÇÃO DE CALLBACK ---
    def update_progress(self, current_frame, total_frames):
        """Atualiza a barra de progresso com base no frame atual (Lendo)"""
        if total_frames > 0:
            # Calcula o progresso de 0.0 a 1.0
            progress = current_frame / total_frames
            
            # Usando .after para atualizar a UI de forma segura a partir da thread
            self.root.after(0, self._update_ui_reading, progress)
            
    def _update_ui_reading(self, progress):
        self.lbl_step.configure(text="Passo 1/3: Lendo Arquivo")
        self.progressbar.set(progress)
        
    
    def update_progress_saving(self, current_frame, total_frames):
        """Atualiza a barra de progresso durante a fase de criação/salvamento"""
        if total_frames > 0:
            progress = current_frame / total_frames
            self.root.after(0, self._update_ui_creating, progress)
            
    def _update_ui_creating(self, progress):
        self.lbl_step.configure(text="Passo 2/3: Criando GIF")
        self.progressbar.set(progress)
        percentage = int(progress * 100)
        
        if percentage == 100:
            self.lbl_step.configure(text="Passo 3/3: Salvando no Disco")
            
    def start_processing(self):
        self.show_screen_processing()
        # Thread para não travar a UI
        threading.Thread(target=self.conversion_logic).start()

    def conversion_logic(self):
        # Chama sua classe original
        # Note: Se self.output_file não tiver diretório, o os.path.dirname pode vir vazio,
        # então ajustamos para salvar na mesma pasta do script se necessário.
        output_dir = os.path.dirname(self.output_file)
        if not output_dir:
            output_dir = "."

        try:
            self.gif_maker.convert_file(
                path=self.selected_file,
                output_path=output_dir, # Sua lib pede o path da pasta, não do arquivo
                scale=0.6,
                less_colors=True,
                max_frames=2000,
                frame_skip=5,
                progress_callback=self.update_progress
            )
            self.gif_maker.save_gif(progress_callback=self.update_progress_saving)
            # Sucesso
            self.root.after(0, self.show_screen_result)
        except Exception as e:
            self.error_message = str(e.args[0])
            self.error_code = e.args[1] if len(e.args) > 1 else -999
            self.root.after(0, self.show_screen_result, True)

    # --- TELA 4: Resultado ---
    def show_screen_result(self, have_error=False):
        self.clear_frame()
        
        if have_error:
            lbl_success = ctk.CTkLabel(self.main_frame, text="Erro durante a conversão!", font=("Roboto Medium", 22), text_color="#FF0000")
            lbl_success.pack(pady=(40, 10))
            lbl_info = ctk.CTkLabel(self.main_frame, text=f"{self.error_message}", font=("Roboto", 12))
            lbl_info.pack(pady=(10, 5))
            if self.error_code in [-1, -2]: # Arquivo ja existe ou caminho inválido
                btn_open_folder = ctk.CTkButton(
                    self.main_frame, 
                    text="📁 Abrir Pasta de Destino", 
                    command=self.open_output_folder,
                    fg_color="#3B8ED0",
                    hover_color="#36719F"
                )
                btn_open_folder.pack(pady=10)
        else:
            lbl_success = ctk.CTkLabel(self.main_frame, text="Concluído!", font=("Roboto Medium", 22), text_color="#2CC985")
            lbl_success.pack(pady=(40, 10))
        
            lbl_info = ctk.CTkLabel(self.main_frame, text="Arquivo salvo em:", font=("Roboto", 12))
            lbl_info.pack(pady=(10, 5))
            
            # --- CONTAINER PARA A CAIXA DE TEXTO E O BOTÃO DE ABRIR ---
            result_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            result_frame.pack(fill="x", padx=30, pady=10)
            result_frame.grid_columnconfigure(0, weight=1) # Faz a entry expandir
            
            # Caixa de texto
            entry_out = ctk.CTkEntry(result_frame, justify="left")
            entry_out.insert(0, self.output_file)
            entry_out.configure(state="readonly")
            entry_out.grid(row=0, column=0, sticky="ew", padx=(0, 10))
            
            # Botão de Ícone para abrir a pasta
            btn_open_folder = ctk.CTkButton(
                result_frame, 
                text="📁", 
                width=40, 
                command=self.open_output_folder,
                fg_color="#3B8ED0",
                hover_color="#36719F"
            )
            btn_open_folder.grid(row=0, column=1)
        
        btn_ok = ctk.CTkButton(self.main_frame, text="Novo Arquivo", command=self.show_screen_initial, width=150)
        btn_ok.pack(pady=30)

    # --- FUNÇÃO PARA ABRIR A PASTA ---
    def open_output_folder(self):
        """Abre o gerenciador de arquivos na pasta onde o GIF foi salvo"""
        folder_path = os.path.dirname(os.path.abspath(self.output_file))
        
        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", folder_path])
        else:  # Linux
            subprocess.Popen(["xdg-open", folder_path])

if __name__ == "__main__":
    app = GifConverterApp()