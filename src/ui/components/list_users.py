import customtkinter as ctk
from utils.user_service import buscar_usuarios_db, buscar_usuario_por_id
from tkinter import messagebox


class ListUsers(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.niveis_map = {1: "Administrador", 2: "Operador", 3: "Vendedor"}
        self.setup_ui()

    def setup_ui(self):
        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(10, 20))
        
        self.label_titulo = ctk.CTkLabel(
            self.header_frame, text="Gestão de Funcionários", 
            font=ctk.CTkFont(family="Arial", size=32, weight="bold")
        )
        self.label_titulo.pack(side="left")

        self.btn_novo = ctk.CTkButton(
            self.header_frame, text="+ Novo Funcionário", 
            fg_color="#27ae60", hover_color="#1e8449",
            command=self.abrir_cadastro_usuario
        )
        self.btn_novo.pack(side="right", pady=(10, 0))

        # --- SEARCH FRAME ---
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=30, pady=(0, 10))

        self.opcao_busca = ctk.StringVar(value="Nome")
        self.menu_filtro = ctk.CTkOptionMenu(
            self.search_frame, 
            values=["ID", "Nome", "Usuário"], 
            variable=self.opcao_busca,
            width=120,
            command=lambda e: self.carregar_usuarios_bd()
        )
        self.menu_filtro.pack(side="left", padx=(0, 10))

        self.entry_busca = ctk.CTkEntry(
            self.search_frame, 
            placeholder_text="Pesquisar funcionário...", 
            width=300
        )
        self.entry_busca.pack(side="left", padx=(0, 10))
        self.entry_busca.bind("<Return>", lambda e: self.carregar_usuarios_bd())

        self.btn_buscar = ctk.CTkButton(self.search_frame, text="Buscar", command=self.carregar_usuarios_bd)
        self.btn_buscar.pack(side="left")

        self.check_inativos = ctk.CTkCheckBox(self.search_frame, text="Ver Inativos", command=self.carregar_usuarios_bd)
        self.check_inativos.pack(side="left", padx=10)

        # Container da Tabela
        self.tabela_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=15)
        self.tabela_frame.pack(fill="both", expand=True, padx=30, pady=10)

        self.carregar_usuarios_bd()

    def carregar_usuarios_bd(self):
        termo_busca = self.entry_busca.get().strip()
        ver_inativos = self.check_inativos.get()
        filtro_atual = self.opcao_busca.get()
        
        usuarios_reais = buscar_usuarios_db(termo_busca, ver_inativos, filtro_atual)

        self.tabela_frame.pack_forget() 

        for child in self.tabela_frame.winfo_children():
            child.destroy()

        # 1. Configuração de Colunas do Container Principal
        self.tabela_frame.grid_columnconfigure((0, 2, 3), weight=1, uniform="col")
        self.tabela_frame.grid_columnconfigure(1, weight=3, uniform="col")

        # --- CABEÇALHOS CENTRALIZADOS (Sem sticky ou anchor manual) ---
        headers = ["ID", "Nome Completo", "Login (Usuário)", "Cargo / Nível"]
        for i, col in enumerate(headers):
            ctk.CTkLabel(
                self.tabela_frame, 
                text=col, 
                font=("Arial", 13, "bold"), 
                text_color="gray"
            ).grid(row=0, column=i, pady=10)

        # --- LINHAS DA TABELA ---
        for i, (u_id, u_nome, u_login, u_nivel, u_ativo) in enumerate(usuarios_reais):
            dados_u = {"id": u_id, "nome": u_nome, "login": u_login, "nivel": u_nivel}
            
            row_idx = i + 1
            cor_fundo = "#333333" if row_idx % 2 == 0 else "transparent"
            if not u_ativo:
                cor_fundo = "#4a2a2a"

            row_frame = ctk.CTkFrame(self.tabela_frame, fg_color=cor_fundo, corner_radius=5, cursor="hand2")
            # Importante: padx=0 para não empurrar a linha em relação ao cabeçalho
            row_frame.grid(row=row_idx, column=0, columnspan=4, sticky="ew", padx=0, pady=2)
            
            # Repete a configuração de pesos exatamente igual
            row_frame.grid_columnconfigure((0, 2, 3), weight=1, uniform="col")
            row_frame.grid_columnconfigure(1, weight=3, uniform="col")

            texto_cargo = self.niveis_map.get(u_nivel, "Desconhecido")

            # Agora os Labels apenas com .grid(), deixando o Tkinter centralizar
            l1 = ctk.CTkLabel(row_frame, text=str(u_id))
            l1.grid(row=0, column=0, pady=8)
            
            l2 = ctk.CTkLabel(row_frame, text=u_nome) 
            l2.grid(row=0, column=1, pady=8)
            
            l3 = ctk.CTkLabel(row_frame, text=u_login)
            l3.grid(row=0, column=2, pady=8)
            
            l4 = ctk.CTkLabel(row_frame, text=texto_cargo, font=("Arial", 12, "italic"))
            l4.grid(row=0, column=3, pady=8)

            for widget in [row_frame, l1, l2, l3, l4]:
                widget.bind("<Double-Button-1>", lambda e, u=dados_u: self.abrir_detalhes_usuario(u))

        self.tabela_frame.pack(fill="both", expand=True, padx=30, pady=10)

    def abrir_cadastro_usuario(self):
        from ui.components.user_regs_modal import UserRegisterModal

        UserRegisterModal(master=self.winfo_toplevel(), ao_salvar=self.carregar_usuarios_bd)

    def abrir_detalhes_usuario(self, usuario):
        from ui.components.user_edit_modal import UserManagerModal
        from utils.auth import UsuarioSessao

        try:
            # 1. Busca os detalhes frescos no banco
            detalhes = buscar_usuario_por_id(usuario['id']) 
            
            # 2. Pega o ID da sessão (Verifique se é .id ou .user_id no seu auth.py)
            id_sessao = UsuarioSessao.id 
            
            if detalhes:
                # 3. Abre o Modal. Usamos winfo_toplevel() para ele ficar por cima de tudo
                UserManagerModal(self.winfo_toplevel(), detalhes, self.carregar_usuarios_bd, id_sessao)
            else:
                messagebox.showerror("Erro", "Não foi possível carregar os detalhes do funcionário no banco.")
                
        except Exception as e:
            messagebox.showerror("Erro de Execução", f"Ocorreu um erro ao tentar abrir o modal: {e}")