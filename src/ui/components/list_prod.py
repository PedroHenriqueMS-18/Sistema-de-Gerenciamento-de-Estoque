import customtkinter as ctk
from utils.product_service import buscar_produtos_db, inativar_produto_db, reativar_produto_bd, atualizar_produto_db,buscar_detalhes_produto_por_id
# Agora importamos o novo modal que vamos criar abaixo
from ui.components.edit_modal import ProductManagerModal 
from tkinter import messagebox

class ListProd(ctk.CTkFrame):
    def __init__(self, master, db_connection=None, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_connection
        self.setup_ui()

    def setup_ui(self):
        # ... (Mantive seu Header e Search Frame como estão) ...
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(10, 20))
        
        self.label_titulo = ctk.CTkLabel(
            self.header_frame, text="SGE Manager - Estoque", 
            font=ctk.CTkFont(family="Arial", size=32, weight="bold")
        )
        self.label_titulo.pack(side="left")

        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=30, pady=(0, 10))

        self.entry_busca = ctk.CTkEntry(self.search_frame, placeholder_text="Pesquisar por nome, EAN ou ID...", width=400)
        self.entry_busca.pack(side="left", padx=(0, 10))
        self.entry_busca.bind("<Return>", lambda e: self.carregar_produtos_bd())

        self.btn_buscar = ctk.CTkButton(self.search_frame, text="Buscar", command=self.carregar_produtos_bd)
        self.btn_buscar.pack(side="left")

        self.check_inativos = ctk.CTkCheckBox(self.search_frame, text="Incluir Inativos", command=self.carregar_produtos_bd)
        self.check_inativos.pack(side="left", padx=10)

        # Container da Tabela
        self.tabela_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=15)
        self.tabela_frame.pack(fill="both", expand=True, padx=30, pady=10)

        self.carregar_produtos_bd()

    def carregar_produtos_bd(self):
        termo_busca = self.entry_busca.get().strip()
        ver_inativos = self.check_inativos.get()
        produtos_reais = buscar_produtos_db(termo_busca, ver_inativos)

        # Técnica de performance: Esconder frame enquanto limpa e recria
        self.tabela_frame.pack_forget() 

        for child in self.tabela_frame.winfo_children():
            child.destroy()

        # Cabeçalho Simples (Apenas o essencial)
        self.tabela_frame.grid_columnconfigure((0, 1), weight=1, uniform="col")
        self.tabela_frame.grid_columnconfigure(2, weight=3, uniform="col")

        headers = ["ID", "Código EAN", "Nome do Produto"]
        for i, col in enumerate(headers):
            ctk.CTkLabel(self.tabela_frame, text=col, font=("Arial", 13, "bold"), text_color="gray").grid(row=0, column=i, pady=10, sticky="nsew")

        # Renderização das linhas
        for i, (p_id, p_ean, p_nome) in enumerate(produtos_reais):
            dados_p = {"id": p_id, "ean": p_ean, "nome": p_nome}
            
            row_idx = i + 1
            cor_fundo = "#333333" if row_idx % 2 == 0 else "transparent"
            
            # Frame da Linha
            row_frame = ctk.CTkFrame(self.tabela_frame, fg_color=cor_fundo, corner_radius=5, cursor="hand2")
            row_frame.grid(row=row_idx, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
            row_frame.grid_columnconfigure((0, 1), weight=1, uniform="col")
            row_frame.grid_columnconfigure(2, weight=3, uniform="col")

            # Labels da linha
            l1 = ctk.CTkLabel(row_frame, text=str(p_id))
            l1.grid(row=0, column=0, pady=8)
            l2 = ctk.CTkLabel(row_frame, text=str(p_ean))
            l2.grid(row=0, column=1, pady=8)
            l3 = ctk.CTkLabel(row_frame, text=p_nome, anchor="center")
            l3.grid(row=0, column=2, pady=8, padx=20, sticky="nsew")

            # BIND DE CLIQUE DUPLO (No frame e em todas as labels dele)
            for widget in [row_frame, l1, l2, l3]:
                widget.bind("<Double-Button-1>", lambda e, p=dados_p: self.abrir_gerenciador(p))

        self.tabela_frame.pack(fill="both", expand=True, padx=30, pady=10)

    def abrir_gerenciador(self, produto):
        # Aqui chamamos o novo modal
        detalhes = buscar_detalhes_produto_por_id(produto['id'])

        if detalhes:
            ProductManagerModal(self.winfo_toplevel(), detalhes, self.carregar_produtos_bd)
        else:
            messagebox.showerror("Erro", "Não foi possivel carregar os detalhes do produto")