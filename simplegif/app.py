import customtkinter as ctk
from tkinter import filedialog
import threading
import os
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

    # --- TELA 3: Processando (Com Barra de Progresso) ---
    def show_screen_processing(self):
        self.clear_frame()
        
        lbl_process = ctk.CTkLabel(self.main_frame, text="Processando seu GIF...", font=("Roboto Medium", 18))
        lbl_process.pack(pady=(60, 20))
        
        # Barra de progresso indeterminada
        self.progressbar = ctk.CTkProgressBar(self.main_frame, width=300)
        self.progressbar.pack(pady=10)
        self.progressbar.configure(mode="indeterminnate")
        self.progressbar.start()

        lbl_wait = ctk.CTkLabel(self.main_frame, text="Isso pode levar alguns segundos.", text_color="gray")
        lbl_wait.pack(pady=10)

    def start_processing(self):
        self.show_screen_processing()
        # Thread para não travar a UI
        threading.Thread(target=self.mock_conversion_logic).start()

    def mock_conversion_logic(self):
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
                frame_skip=5
            )
            # Sucesso
            self.root.after(0, self.show_screen_result)
        except Exception as e:
            print(f"Erro: {e}")
            # Aqui você poderia criar uma tela de erro se quisesse

    # --- TELA 4: Resultado ---
    def show_screen_result(self):
        self.clear_frame()
        
        lbl_success = ctk.CTkLabel(self.main_frame, text="Concluído!", font=("Roboto Medium", 22), text_color="#2CC985")
        lbl_success.pack(pady=(40, 10))
        
        lbl_info = ctk.CTkLabel(self.main_frame, text="Arquivo salvo em:", font=("Roboto", 12))
        lbl_info.pack(pady=(10, 5))
        
        # Caixa de texto para o usuário poder copiar o caminho se quiser
        entry_out = ctk.CTkEntry(self.main_frame, justify="center")
        entry_out.insert(0, self.output_file)
        entry_out.configure(state="readonly")
        entry_out.pack(fill="x", padx=40, pady=10)
        
        btn_ok = ctk.CTkButton(self.main_frame, text="Novo Arquivo", command=self.show_screen_initial, width=150)
        btn_ok.pack(pady=30)

if __name__ == "__main__":
    app = GifConverterApp()