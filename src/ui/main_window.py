import customtkinter as ctk
from ui.components.list_prod import ListProd
from ui.components.home import Home

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

        self.btn_home = ctk.CTkButton(self.sidebar, text="Dashboard", command=self.show_home)
        self.btn_home.pack(pady=10, padx=20, fill="x")

        self.btn_prod = ctk.CTkButton(self.sidebar, text="Estoque", command=self.mostrar_produtos)
        self.btn_prod.pack(pady=10, padx=20, fill="x")

        self.area_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.area_principal.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.show_home()

    def select_aba(self, btn_clicked):
        buttons = [self.btn_home, self.btn_prod]

        for btn in buttons:
            if btn == btn_clicked:
                btn.configure(fg_color="#333333", border_width=1, border_color="#f39c12", hover_color="#404040")
            else:
                btn.configure(fg_color="transparent", border_width=0, hover_color="#2b2b2b")

    """Remove todos os widgets atualmente presentes na área de conteúdo principal da janela."""
    def clean_screen(self):
        for widget in self.area_principal.winfo_children():
            widget.destroy()

    """Limpa a tela e instancia o componente Home para exibir o dashboard inicial."""
    def show_home(self):
        self.clean_screen()
        self.select_aba(self.btn_home)
        self.tela = Home(master=self.area_principal, funcao_estoque=self.mostrar_produtos)
        self.tela.pack(fill="both", expand=True)

    """Limpa a tela e carrega o componente ListProd para visualização e gestão dos produtos no estoque."""
    def mostrar_produtos(self):
        self.clean_screen()
        self.select_aba(self.btn_prod)
        self.tela = ListProd(master=self.area_principal, db_connection=self.db)
        self.tela.pack(fill="both", expand=True)