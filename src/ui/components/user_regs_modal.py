import customtkinter as ctk
from tkinter import messagebox
from utils.user_service import cadastrar_usuario_db

class UserRegisterModal(ctk.CTkToplevel):
    def __init__(self, master, ao_salvar):
        super().__init__(master)
        
        self.ao_salvar = ao_salvar
        self.title("SGE - Cadastrar Novo Funcionário")
        self.geometry("680x550")
        self.resizable(False, False)
        
        self.transient(master)
        self.grab_set()
        
        self.setup_ui()

    def setup_ui(self):
        # Título
        ctk.CTkLabel(self, text="Cadastrar Funcionário", font=("Arial", 28, "bold")).pack(pady=(30, 5))
        ctk.CTkLabel(self, text="Preencha os dados de acesso do colaborador", font=("Arial", 12), text_color="gray").pack(pady=(0, 20))

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=40)

        # Coluna da Esquerda (Dados Pessoais)
        self.frame_esq = ctk.CTkFrame(self.container, corner_radius=15)
        self.frame_esq.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.label_nome = ctk.CTkLabel(self.frame_esq, text="Nome Completo")
        self.label_nome.pack(pady=(15, 0), padx=20, anchor="w")
        self.entry_nome = ctk.CTkEntry(self.frame_esq, width=220, height=40)
        self.entry_nome.pack(pady=(5, 10), padx=20)

        self.label_cpf = ctk.CTkLabel(self.frame_esq, text="CPF")
        self.label_cpf.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_cpf = ctk.CTkEntry(self.frame_esq, width=220, height=40)
        self.entry_cpf.pack(pady=(5, 10), padx=20)

        self.label_login = ctk.CTkLabel(self.frame_esq, text="Login (Usuário)")
        self.label_login.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_login = ctk.CTkEntry(self.frame_esq, width=220, height=40)
        self.entry_login.pack(pady=(5, 20), padx=20)

        # Coluna da Direita (Segurança e Nível)
        self.frame_dir = ctk.CTkFrame(self.container, corner_radius=15)
        self.frame_dir.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.label_cat = ctk.CTkLabel(self.frame_dir, text="Cargo / Nível")
        self.label_cat.pack(pady=(15, 0), padx=20, anchor="w")
        self.combo_nivel = ctk.CTkOptionMenu(self.frame_dir, values=["Administrador", "Operador", "Vendedor"], width=220, height=40)
        self.combo_nivel.pack(pady=(5, 10), padx=20)

        self.label_senha = ctk.CTkLabel(self.frame_dir, text="Senha")
        self.label_senha.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_senha = ctk.CTkEntry(self.frame_dir, width=220, height=40, show="*")
        self.entry_senha.pack(pady=(5, 10), padx=20)

        self.label_confirm = ctk.CTkLabel(self.frame_dir, text="Confirmar Senha")
        self.label_confirm.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_confirm = ctk.CTkEntry(self.frame_dir, width=220, height=40, show="*")
        self.entry_confirm.pack(pady=(5, 20), padx=20)

        # Botão Salvar
        self.btn_salvar = ctk.CTkButton(self, text="FINALIZAR CADASTRO", fg_color="#27ae60", hover_color="#219150", 
                                        height=45, font=("Arial", 14, "bold"), command=self.salvar_usuario)
        self.btn_salvar.pack(pady=(20, 30), padx=60, fill="x")

    def limpar_campos(self):
        """Limpa todos os campos de entrada de texto após o cadastro."""
        self.entry_nome.delete(0, 'end')
        self.entry_cpf.delete(0, 'end')
        self.entry_login.delete(0, 'end')
        self.entry_senha.delete(0, 'end')
        self.entry_confirm.delete(0, 'end')
        self.combo_nivel.set("Vendedor") # Opcional: reseta o nível para o padrão
        self.entry_nome.focus()

    def salvar_usuario(self):
        niveis_map = {"Administrador": 1, "Operador": 2, "Vendedor": 3}

        dados = {
            "nome": self.entry_nome.get().strip(),
            "cpf": self.entry_cpf.get().strip(),
            "login": self.entry_login.get().strip(),
            "nivel": niveis_map.get(self.combo_nivel.get(), 3),
            "senha": self.entry_senha.get(),
            "confirmacao": self.entry_confirm.get()
        }

        # Validações Básicas
        if not all([dados["nome"], dados["cpf"], dados["login"], dados["senha"]]):
            messagebox.showwarning("Aviso", "Todos os campos são obrigatórios!")
            return

        if dados["senha"] != dados["confirmacao"]:
            messagebox.showerror("Erro", "As senhas não coincidem!")
            return

        # Chamada para o Service
        if cadastrar_usuario_db(dados):
            messagebox.showinfo("Sucesso", f"Usuário {dados['login']} cadastrado!")
            if self.ao_salvar:
                self.ao_salvar()

            self.limpar_campos()
        