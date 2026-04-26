import customtkinter as ctk
# Vamos assumir que você criará essas funções no fornecedor_service.py
from utils.fornec_service import buscar_fornecedores_db, buscar_fornecedor_por_id
from tkinter import messagebox

class ListFornec(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # Removi o niveis_map pois fornecedor não tem "cargo"
        self.setup_ui()

    def setup_ui(self):
        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(10, 20))
        
        self.label_titulo = ctk.CTkLabel(
            self.header_frame, text="Gestão de Fornecedores", 
            font=ctk.CTkFont(family="Arial", size=32, weight="bold")
        )
        self.label_titulo.pack(side="left")

        self.btn_novo = ctk.CTkButton(
            self.header_frame, text="+ Novo Fornecedor", 
            fg_color="#27ae60", hover_color="#1e8449",
            command=self.abrir_cadastro_fornecedor # Ajustado nome
        )
        self.btn_novo.pack(side="right", pady=(10, 0))

        # --- SEARCH FRAME ---
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=30, pady=(0, 10))

        self.opcao_busca = ctk.StringVar(value="Nome")
        self.menu_filtro = ctk.CTkOptionMenu(
            self.search_frame, 
            values=["ID", "Nome", "CNPJ"], # Filtros de fornecedor
            variable=self.opcao_busca,
            width=120,
            command=lambda e: self.carregar_fornecedores_bd()
        )
        self.menu_filtro.pack(side="left", padx=(0, 10))

        self.entry_busca = ctk.CTkEntry(
            self.search_frame, 
            placeholder_text="Pesquisar por nome ou CNPJ...", 
            width=300
        )
        self.entry_busca.pack(side="left", padx=(0, 10))
        self.entry_busca.bind("<Return>", lambda e: self.carregar_fornecedores_bd())

        self.btn_buscar = ctk.CTkButton(self.search_frame, text="Buscar", command=self.carregar_fornecedores_bd)
        self.btn_buscar.pack(side="left")

        self.check_inativos = ctk.CTkCheckBox(self.search_frame, text="Ver Inativos", command=self.carregar_fornecedores_bd)
        self.check_inativos.pack(side="left", padx=10)

        # Container da Tabela
        self.tabela_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=15)
        self.tabela_frame.pack(fill="both", expand=True, padx=30, pady=10)

        self.carregar_fornecedores_bd()

    def carregar_fornecedores_bd(self):
        termo_busca = self.entry_busca.get().strip()
        ver_inativos = self.check_inativos.get()
        filtro_atual = self.opcao_busca.get()
        
        # Chama o serviço de fornecedores
        fornecedores_reais = buscar_fornecedores_db(termo_busca, ver_inativos, filtro_atual)

        self.tabela_frame.pack_forget() 

        for child in self.tabela_frame.winfo_children():
            child.destroy()

        # Configuração de Colunas (ID, Nome Fantasia, CNPJ, Telefone)
        self.tabela_frame.grid_columnconfigure((0, 2, 3), weight=1, uniform="col")
        self.tabela_frame.grid_columnconfigure(1, weight=3, uniform="col")

        # --- CABEÇALHOS ---
        headers = ["ID", "Nome Fantasia", "CNPJ", "Telefone"]
        for i, col in enumerate(headers):
            ctk.CTkLabel(
                self.tabela_frame, 
                text=col, 
                font=("Arial", 13, "bold"), 
                text_color="gray"
            ).grid(row=0, column=i, pady=10)

        # --- LINHAS DA TABELA ---
        for i, (f_id, f_nome, f_cnpj, f_tel, f_ativo) in enumerate(fornecedores_reais):
            dados_f = {"id": f_id, "nome": f_nome, "cnpj": f_cnpj}
            
            row_idx = i + 1
            cor_fundo = "#333333" if row_idx % 2 == 0 else "transparent"
            if not f_ativo:
                cor_fundo = "#4a2a2a" # Vermelho escuro para inativos

            row_frame = ctk.CTkFrame(self.tabela_frame, fg_color=cor_fundo, corner_radius=5, cursor="hand2")
            row_frame.grid(row=row_idx, column=0, columnspan=4, sticky="ew", padx=0, pady=2)
            
            row_frame.grid_columnconfigure((0, 2, 3), weight=1, uniform="col")
            row_frame.grid_columnconfigure(1, weight=3, uniform="col")

            # ID
            l1 = ctk.CTkLabel(row_frame, text=str(f_id))
            l1.grid(row=0, column=0, pady=8)
            
            # Nome Fantasia
            l2 = ctk.CTkLabel(row_frame, text=f_nome, font=("Arial", 12, "bold")) 
            l2.grid(row=0, column=1, pady=8)
            
            # CNPJ
            l3 = ctk.CTkLabel(row_frame, text=f_cnpj)
            l3.grid(row=0, column=2, pady=8)
            
            # Telefone
            l4 = ctk.CTkLabel(row_frame, text=f_tel if f_tel else "N/A")
            l4.grid(row=0, column=3, pady=8)

            # Bind para abrir detalhes ao clicar duas vezes
            for widget in [row_frame, l1, l2, l3, l4]:
                widget.bind("<Double-Button-1>", lambda e, f=dados_f: self.abrir_detalhes_fornecedor(f))

        self.tabela_frame.pack(fill="both", expand=True, padx=30, pady=10)

    def abrir_cadastro_fornecedor(self):
        # Aqui você importará o Modal de Cadastro de Fornecedor que vamos criar
        from ui.components.fornec_regs_modal import FornecRegisterModal
        FornecRegisterModal(master=self.winfo_toplevel(), ao_salvar=self.carregar_fornecedores_bd)

    def abrir_detalhes_fornecedor(self, fornecedor):
        # Aqui você importará o Modal de Edição de Fornecedor
        from ui.components.fornec_edit_modal import FornecEditModal
        
        try:
            detalhes = buscar_fornecedor_por_id(fornecedor['id']) 
            
            if detalhes:
                FornecEditModal(self.winfo_toplevel(), detalhes, self.carregar_fornecedores_bd)
            else:
                messagebox.showerror("Erro", "Não foi possível carregar os detalhes do fornecedor.")
                
        except Exception as e:
            messagebox.showerror("Erro de Execução", f"Erro ao abrir detalhes: {e}")