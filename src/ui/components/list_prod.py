import customtkinter as ctk
from ui.components.edit_modal import EditModal

class ListProd(ctk.CTkFrame):
    """Componente de interface que exibe a listagem de produtos do estoque em formato de tabela."""
    
    def __init__(self, master, db_connection=None, **kwargs):
        """Inicializa o frame da lista de produtos e configura a conexão com o banco."""
        super().__init__(master, **kwargs)
        self.db = db_connection
        self.configure(fg_color="transparent")
        self.setup_ui()

    def setup_ui(self):
        """Responsável pela construção visual da tabela e do cabeçalho."""
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(10, 20))
        
        self.label_titulo = ctk.CTkLabel(
            self.header_frame, text="Lista de Estoque", 
            font=ctk.CTkFont(family="Arial", size=32, weight="bold")
        )
        self.label_titulo.pack(side="left", anchor="w")

        self.tabela_frame = ctk.CTkScrollableFrame(
            self, fg_color="#2b2b2b", corner_radius=15,
            border_width=1, border_color="#3d3d3d"
        )
        self.tabela_frame.pack(fill="both", expand=True, padx=30, pady=10)

        self.tabela_frame.grid_columnconfigure(0, weight=1, uniform="col")
        self.tabela_frame.grid_columnconfigure(1, weight=3, uniform="col")
        self.tabela_frame.grid_columnconfigure(2, weight=1, uniform="col")
        self.tabela_frame.grid_columnconfigure(3, weight=1, uniform="col")
        self.tabela_frame.grid_columnconfigure(4, weight=2, uniform="col")

        colunas = ["ID", "Nome", "Preço", "Qtd", "Ações"]
        for i, col in enumerate(colunas):
            lbl = ctk.CTkLabel(self.tabela_frame, text=col, font=("Arial", 14, "bold"), text_color="gray")
            lbl.grid(row=0, column=i, pady=15, sticky="nsew")

        produtos_exemplo = [(1, "Arroz Tio João", "R$ 30,00", 50), (2, "Feijão Preto", "R$ 9,50", 25)]

        for i, (p_id, p_nome, p_preco, p_qtd) in enumerate(produtos_exemplo):
            dados_p = {"id": p_id, "nome": p_nome, "preco": p_preco, "qtd": p_qtd}
            
            row_idx = i + 1
            cor_fundo = "#333333" if row_idx % 2 == 0 else "transparent" 
            
            row_frame = ctk.CTkFrame(self.tabela_frame, fg_color=cor_fundo, corner_radius=0)
            row_frame.grid(row=row_idx, column=0, columnspan=5, sticky="ew")
            
            row_frame.grid_columnconfigure(0, weight=1, uniform="col")
            row_frame.grid_columnconfigure(1, weight=3, uniform="col")
            row_frame.grid_columnconfigure(2, weight=1, uniform="col")
            row_frame.grid_columnconfigure(3, weight=1, uniform="col")
            row_frame.grid_columnconfigure(4, weight=2, uniform="col")
           
            ctk.CTkLabel(row_frame, text=str(p_id)).grid(row=0, column=0, pady=10, sticky="nsew")
            ctk.CTkLabel(row_frame, text=p_nome, anchor="w").grid(row=0, column=1, pady=10, sticky="nsew", padx=20)
            ctk.CTkLabel(row_frame, text=p_preco).grid(row=0, column=2, pady=10, sticky="nsew")
            ctk.CTkLabel(row_frame, text=str(p_qtd)).grid(row=0, column=3, pady=10, sticky="nsew")
            
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=4, sticky="nsew")
            btn_container = ctk.CTkFrame(actions_frame, fg_color="transparent")
            btn_container.pack(expand=True)
            
            ctk.CTkButton(btn_container, text="📝 Editar", width=70, cursor="hand2", 
                          command=lambda p=dados_p: self.abrir_edicao(p)).pack(side="left", padx=2)
            
            ctk.CTkButton(btn_container, text="🗑️ Deletar", width=70, fg_color="red", cursor="hand2").pack(side="left", padx=2)
    
    def abrir_edicao(self, produto):
        """Instancia o modal de edição passando os dados da linha selecionada."""
        self.modal = EditModal(
            master=self, 
            produto_data=produto, 
            on_save_callback=self.salvar_edicao_banco
        )

    def salvar_edicao_banco(self, novos_dados):
        """Recebe os dados atualizados do modal para futura integração com o banco."""
        print(f"Dados prontos para o banco: {novos_dados}")