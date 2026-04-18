import customtkinter as ctk
from ui.components.list_prod import ListProd
from ui.components.home import Home
from utils.auth import UsuarioSessao
from ui.components.list_users import ListUsers

"""Define a janela principal do sistema, gerenciando a navegação entre diferentes telas e componentes."""
class MainWindow(ctk.CTk):
    """Inicializa a interface principal, configura o layout de grade e constrói a barra lateral de navegação."""
    def __init__(self, db_connection=None):
        super().__init__()
        self.db = db_connection
        self.after(0, lambda: self.state('zoomed'))
        self.title("SGE Manager")

        self.grid_columnconfigure(0, minsize=250)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=350, corner_radius=5)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="💧 SGE Manager", font=("Arial", 22, "bold")).pack(pady=30)

        # Botões padrão
        self.btn_home = ctk.CTkButton(self.sidebar, text="Dashboard", command=self.show_home)
        self.btn_home.pack(pady=10, padx=20, fill="x")

        self.btn_prod = ctk.CTkButton(self.sidebar, text="Estoque", command=self.mostrar_produtos)
        self.btn_prod.pack(pady=10, padx=20, fill="x")

        # --- BOTÃO CONDICIONAL: GESTÃO DE USUÁRIOS ---
        # Só inicializamos como None para evitar erro na função select_aba
        self.btn_users = None 

        if UsuarioSessao.nivel == 1:
            self.btn_users = ctk.CTkButton(
                self.sidebar, 
                text="Gerenciar Funcionários", 
                fg_color="#1f538d", # Cor azulada para destacar função administrativa
                command=self.mostrar_usuarios
            )
            self.btn_users.pack(pady=10, padx=20, fill="x")

        self.area_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.area_principal.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.show_home()

    def select_aba(self, btn_clicked):
        # Adicionamos o self.btn_users na lista de botões a serem resetados (se ele existir)
        buttons = [self.btn_home, self.btn_prod]
        if self.btn_users:
            buttons.append(self.btn_users)

        for btn in buttons:
            if btn == btn_clicked:
                btn.configure(fg_color="#333333", border_width=1, border_color="#f39c12", hover_color="#404040")
            else:
                # Cor especial para o botão de usuários quando não selecionado (se existir)
                if btn == self.btn_users:
                     btn.configure(fg_color="#1f538d", border_width=0, hover_color="#14375e")
                else:
                    btn.configure(fg_color="transparent", border_width=0, hover_color="#2b2b2b")

    def clean_screen(self):
        for widget in self.area_principal.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clean_screen()
        self.select_aba(self.btn_home)
        self.tela = Home(master=self.area_principal, funcao_estoque=self.mostrar_produtos)
        self.tela.pack(fill="both", expand=True)

    def mostrar_produtos(self):
        self.clean_screen()
        self.select_aba(self.btn_prod)
        self.tela = ListProd(master=self.area_principal, db_connection=self.db)
        self.tela.pack(fill="both", expand=True)

    # --- NOVA FUNÇÃO PARA A TELA DE USUÁRIOS ---
    def mostrar_usuarios(self):
        self.clean_screen()
        self.select_aba(self.btn_users)
        self.tela = ListUsers(master=self.area_principal)
        self.tela.pack(fill="both", expand=True)