import customtkinter as ctk

class MainWindow(ctk.CTk):
    def __init__(self, db_connection=None):
        super().__init__()

        self.db = db_connection
         
        self.after(0, lambda: self.state('zoomed'))
        self.title("SGE Manager - Painel de Controle")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=5)
        self.sidebar.grid(row=0, column=0, sticky="nsew")       
       
        self.logo_label = ctk.CTkLabel(self.sidebar, text="SGE Manager", font=("Arial", 22, "bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=30)
        
        self.btn_estoque = ctk.CTkButton(
            self.sidebar, text="Estoque", 
            fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w",
            command=lambda: print("Indo para Estoque...")
        )
        self.btn_estoque.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_cadastro = ctk.CTkButton(
            self.sidebar, text="Novo Produto", 
            fg_color="transparent", text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"), anchor="w",
            command=lambda: print("Indo para Cadastro...")
        )
        self.btn_cadastro.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.area_principal = ctk.CTkFrame(self, corner_radius=15)
        self.area_principal.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.msg_boas_vindas = ctk.CTkLabel(
            self.area_principal, 
            text="Bem-vindo ao Sistema de Estoque!\nSelecione uma opção no menu lateral.", 
            font=("Arial", 18)
        )
        self.msg_boas_vindas.pack(expand=True)