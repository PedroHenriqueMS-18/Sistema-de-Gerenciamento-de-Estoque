import customtkinter as ctk
from tkinter import messagebox 
from ui.components.list_prod import ListProd
from ui.components.home import Home
from utils.auth import UsuarioSessao
from ui.components.list_users import ListUsers
from ui.components.list_fornec import ListFornec
from ui.components.financeiro import Financeiro
from ui.components.pedidos_compra import PedidosCompra

class MainWindow(ctk.CTk):
    def __init__(self, db_connection=None):
        super().__init__()
        self.db = db_connection
        self.after(0, lambda: self.state('zoomed'))
        self.title("SGE Manager")

        # Configuração de Grid da Janela Principal
        self.grid_columnconfigure(0, minsize=250)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=5)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="🏢 SGE Manager", font=("Arial", 22, "bold")).pack(pady=30)

        # Botões de Navegação Padrão
        self.btn_home = ctk.CTkButton(self.sidebar, text="Dashboard", command=self.show_home)
        self.btn_home.pack(pady=10, padx=20, fill="x")

        self.btn_prod = ctk.CTkButton(self.sidebar, text="Estoque", command=self.mostrar_produtos)
        self.btn_prod.pack(pady=10, padx=20, fill="x")

        # 🔧 CORREÇÃO 1: Guardando a referência correta do botão de fornecedores na instância (self.btn_fornec)
        self.btn_fornec = ctk.CTkButton(self.sidebar, text="Fornecedores", command=self.mostrar_fornec)
        self.btn_fornec.pack(pady=10, padx=20, fill="x")

        # Visível pra Nível 1 e Nível 2 — igual Estoque/Fornecedores, sem restrição de nível
        self.btn_compras = ctk.CTkButton(self.sidebar, text="📦 Pedidos de Compra", command=self.mostrar_compras)
        self.btn_compras.pack(pady=10, padx=20, fill="x")

        # --- BOTÃO CONDICIONAL: GESTÃO DE USUÁRIOS ---
        self.btn_users = None 
        if UsuarioSessao.nivel == 1:
            self.btn_users = ctk.CTkButton(
                self.sidebar, 
                text="Gerenciar Funcionários", 
                fg_color="#1f538d",
                hover_color="#14375e",
                command=self.mostrar_usuarios
            )
            self.btn_users.pack(pady=10, padx=20, fill="x")

        # --- BOTÃO CONDICIONAL: FINANCEIRO (Contas a Pagar / a Receber) ---
        self.btn_financeiro = None
        if UsuarioSessao.nivel == 1:
            self.btn_financeiro = ctk.CTkButton(
                self.sidebar,
                text="💰 Financeiro",
                fg_color="#1f538d",
                hover_color="#14375e",
                command=self.mostrar_financeiro
            )
            self.btn_financeiro.pack(pady=10, padx=20, fill="x")

        # --- BOTÃO DE LOGOUT (Fixado no final da sidebar) ---
        self.btn_logout = ctk.CTkButton(
            self.sidebar, 
            text="Sair / Trocar Usuário", 
            fg_color="#c0392b", 
            hover_color="#a93226",
            command=self.fazer_logout
        )
        self.btn_logout.pack(side="bottom", pady=30, padx=20, fill="x")

        # --- ÁREA PRINCIPAL CONTAINER ---
        self.area_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.area_principal.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Inicializa o sistema mostrando a Dashboard executiva
        self.show_home()

    def fazer_logout(self):
        """Limpa a sessão atual, fecha a janela principal e retorna de forma segura para o Login."""
        confirmar = messagebox.askyesno("Encerrar Sessão", "Deseja realmente sair e trocar de usuário?")
        
        if confirmar:
            UsuarioSessao.id = None
            UsuarioSessao.nome = None
            UsuarioSessao.nivel = None
            
            self.destroy()
            
            from ui.login import LoginWindow

            def reload_sistem():
                from ui.main_window import MainWindow
                app = MainWindow(db_connection=self.db)
                app.mainloop()

            app_login = LoginWindow(on_login_success=reload_sistem)
            app_login.mainloop()

    def select_aba(self, btn_clicked):
        """Gerencia visualmente as cores de ativação das abas laterais da Sidebar."""
        # 🔧 CORREÇÃO 2: Unificando dinamicamente todos os botões no mapeamento de estado visual
        buttons = [self.btn_home, self.btn_prod, self.btn_fornec, self.btn_compras]
        if self.btn_users:
            buttons.append(self.btn_users)
        if self.btn_financeiro:
            buttons.append(self.btn_financeiro)

        for btn in buttons:
            if btn == btn_clicked:
                # Destaque com borda laranja para a aba selecionada
                btn.configure(fg_color="#333333", border_width=1, border_color="#f39c12", hover_color="#404040")
            else:
                # Restaura a cor padrão de cada botão de forma isolada
                if btn in (self.btn_users, self.btn_financeiro):
                     btn.configure(fg_color="#1f538d", border_width=0, hover_color="#14375e")
                else:
                    btn.configure(fg_color="transparent", border_width=0, hover_color="#2b2b2b")

    def clean_screen(self):
        """Limpa a área central eliminando resíduos de memória dos widgets anteriores."""
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

    def mostrar_usuarios(self):
        self.clean_screen()
        self.select_aba(self.btn_users)
        self.tela = ListUsers(master=self.area_principal)
        self.tela.pack(fill="both", expand=True)

    def mostrar_fornec(self):
        self.clean_screen()
        # 🔧 CORREÇÃO 3: Vinculando a aba ao botão correto para evitar falhas em níveis operacionais
        self.select_aba(self.btn_fornec)
        self.tela = ListFornec(master=self.area_principal)
        self.tela.pack(fill="both", expand=True)

    def mostrar_financeiro(self):
        self.clean_screen()
        self.select_aba(self.btn_financeiro)
        self.tela = Financeiro(master=self.area_principal)
        self.tela.pack(fill="both", expand=True)

    def mostrar_compras(self):
        self.clean_screen()
        self.select_aba(self.btn_compras)
        self.tela = PedidosCompra(master=self.area_principal)
        self.tela.pack(fill="both", expand=True)