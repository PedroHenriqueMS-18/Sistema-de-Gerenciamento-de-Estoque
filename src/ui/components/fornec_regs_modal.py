import customtkinter as ctk
from tkinter import messagebox
from utils.fornec_service import cadastrar_fornecedor_db

class FornecRegisterModal(ctk.CTkToplevel):
    def __init__(self, master, ao_salvar):
        super().__init__(master)
        
        self.ao_salvar = ao_salvar
        self.title("SGE - Cadastrar Novo Fornecedor")
        self.geometry("700x600")
        self.resizable(False, False)
        
        self.transient(master)
        self.grab_set()
        
        self.setup_ui()

    def setup_ui(self):
        # Título
        ctk.CTkLabel(self, text="Cadastrar Fornecedor", font=("Arial", 28, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Preencha os dados comerciais da empresa", font=("Arial", 12), text_color="gray").pack(pady=(0, 20))

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=40)

        # Coluna da Esquerda (Identificação)
        self.frame_esq = ctk.CTkFrame(self.container, corner_radius=15)
        self.frame_esq.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.label_fantasia = ctk.CTkLabel(self.frame_esq, text="Nome Fantasia")
        self.label_fantasia.pack(pady=(15, 0), padx=20, anchor="w")
        self.entry_fantasia = ctk.CTkEntry(self.frame_esq, width=250, height=35)
        self.entry_fantasia.pack(pady=(5, 10), padx=20)

        self.label_razao = ctk.CTkLabel(self.frame_esq, text="Razão Social")
        self.label_razao.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_razao = ctk.CTkEntry(self.frame_esq, width=250, height=35)
        self.entry_razao.pack(pady=(5, 10), padx=20)

        self.label_cnpj = ctk.CTkLabel(self.frame_esq, text="CNPJ")
        self.label_cnpj.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_cnpj = ctk.CTkEntry(self.frame_esq, width=250, height=35, placeholder_text="00.000.000/0000-00")
        self.entry_cnpj.pack(pady=(5, 20), padx=20)

        # Coluna da Direita (Contato e Localização)
        self.frame_dir = ctk.CTkFrame(self.container, corner_radius=15)
        self.frame_dir.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.label_tel = ctk.CTkLabel(self.frame_dir, text="Telefone")
        self.label_tel.pack(pady=(15, 0), padx=20, anchor="w")
        self.entry_tel = ctk.CTkEntry(self.frame_dir, width=250, height=35, placeholder_text="(00) 00000-0000")
        self.entry_tel.pack(pady=(5, 10), padx=20)

        self.label_email = ctk.CTkLabel(self.frame_dir, text="E-mail")
        self.label_email.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_email = ctk.CTkEntry(self.frame_dir, width=250, height=35)
        self.entry_email.pack(pady=(5, 10), padx=20)

        self.label_end = ctk.CTkLabel(self.frame_dir, text="Endereço Completo")
        self.label_end.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_end = ctk.CTkEntry(self.frame_dir, width=250, height=35)
        self.entry_end.pack(pady=(5, 20), padx=20)

        # Botão Salvar
        self.btn_salvar = ctk.CTkButton(self, text="FINALIZAR CADASTRO", fg_color="#27ae60", hover_color="#219150", 
                                        height=45, font=("Arial", 14, "bold"), command=self.salvar_fornecedor)
        self.btn_salvar.pack(pady=(20, 30), padx=60, fill="x")

    def limpar_campos(self):
        self.entry_fantasia.delete(0, 'end')
        self.entry_razao.delete(0, 'end')
        self.entry_cnpj.delete(0, 'end')
        self.entry_tel.delete(0, 'end')
        self.entry_email.delete(0, 'end')
        self.entry_end.delete(0, 'end')
        self.entry_fantasia.focus()

    def salvar_fornecedor(self):
        dados = {
            "nome_fantasia": self.entry_fantasia.get().strip(),
            "razao_social": self.entry_razao.get().strip(),
            "cnpj": self.entry_cnpj.get().strip(),
            "telefone": self.entry_tel.get().strip(),
            "email": self.entry_email.get().strip(),
            "endereco": self.entry_end.get().strip()
        }

        # Validação: Nome Fantasia e CNPJ são cruciais
        if not dados["nome_fantasia"] or not dados["cnpj"]:
            messagebox.showwarning("Aviso", "Nome Fantasia e CNPJ são obrigatórios!")
            return

        # Chamada para o Service de Fornecedor
        if cadastrar_fornecedor_db(dados):
            messagebox.showinfo("Sucesso", f"Fornecedor {dados['nome_fantasia']} cadastrado!")
            if self.ao_salvar:
                self.ao_salvar()
            self.destroy()