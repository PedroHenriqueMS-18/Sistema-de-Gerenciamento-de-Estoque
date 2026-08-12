import customtkinter as ctk
from utils.pdv_service import buscar_produtos_pdv


class ModalPesquisaProduto(ctk.CTkToplevel):
    """
    Modal de pesquisa de produtos do PDV (atalho F1).
    Permite localizar produtos pelo código de barras (EAN) ou pelo nome/descrição
    e devolve o item escolhido para a tela de vendas via callback 'ao_selecionar'.
    """
    def __init__(self, master, ao_selecionar):
        super().__init__(master)

        self.ao_selecionar = ao_selecionar  # Função do MainPDV que recebe a tupla do produto
        self.resultados_atuais = []  # Cache da última busca renderizada na tabela

        # Configurações da Janela
        self.title("Pesquisar Produto (F1)")
        self.geometry("780x560")
        self.configure(fg_color="#1a1a1a")

        # Garante que o usuário interaja apenas com essa janela (Modal)
        self.transient(master)
        self.grab_set()

        self.setup_ui()
        self.configurar_binds()

        # Dispara uma busca inicial vazia -> lista os produtos mais recentes cadastrados
        self.executar_busca(inicial=True)

    def setup_ui(self):
        ctk.CTkLabel(self, text="PESQUISAR PRODUTO", font=("Arial", 20, "bold"), text_color="#3498db").pack(pady=(15, 10))

        # --- CAMPO DE BUSCA ---
        self.busca_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.busca_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.entry_termo = ctk.CTkEntry(
            self.busca_frame,
            placeholder_text="Digite o código de barras ou o nome do produto...",
            height=45,
            font=("Arial", 16),
            fg_color="#2b2b2b"
        )
        self.entry_termo.pack(side="left", fill="x", expand=True)
        self.entry_termo.focus()

        self.btn_buscar = ctk.CTkButton(
            self.busca_frame,
            text="BUSCAR",
            command=self.executar_busca,
            fg_color="#3498db",
            hover_color="#2980b9",
            height=45,
            width=110,
            font=("Arial", 14, "bold")
        )
        self.btn_buscar.pack(side="left", padx=(10, 0))

        # --- TABELA DE RESULTADOS ---
        self.table_weights = [1, 2, 4, 1, 1]

        self.tabela_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.tabela_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.render_cabecalho()

        # --- RODAPÉ DE ORIENTAÇÃO ---
        self.lbl_dica = ctk.CTkLabel(
            self,
            text="Dê um duplo clique no produto para adicioná-lo à venda atual. (ESC fecha a pesquisa)",
            font=("Arial", 11),
            text_color="gray"
        )
        self.lbl_dica.pack(pady=(0, 15))

    def render_cabecalho(self):
        headers = ["CÓDIGO", "EAN", "PRODUTO", "PREÇO", "ESTOQUE"]

        header_row = ctk.CTkFrame(self.tabela_frame, fg_color="#3d3d3d", corner_radius=0)
        header_row.pack(fill="x", side="top", pady=(0, 5))

        for i, texto in enumerate(headers):
            lbl = ctk.CTkLabel(
                header_row,
                text=texto,
                font=("Arial", 12, "bold"),
                text_color="gray",
                anchor="center"
            )
            lbl.grid(row=0, column=i, sticky="nsew", pady=8)
            header_row.grid_columnconfigure(i, weight=self.table_weights[i], uniform="col_pesquisa")

    def configurar_binds(self):
        self.entry_termo.bind("<Return>", lambda e: self.executar_busca())
        self.bind("<Escape>", lambda e: self.destroy())

    def executar_busca(self, inicial=False):
        termo = self.entry_termo.get().strip()

        # Na primeira abertura, sem termo digitado, não força uma query vazia no banco
        if not termo and inicial:
            self.resultados_atuais = []
            self.renderizar_resultados(mensagem_vazia="Digite um código ou nome para pesquisar.")
            return

        if not termo:
            return

        self.resultados_atuais = buscar_produtos_pdv(termo)
        self.renderizar_resultados()

    def renderizar_resultados(self, mensagem_vazia="Nenhum produto encontrado."):
        # Remove apenas as linhas de resultado, preservando o cabeçalho fixo (primeiro filho)
        for widget in self.tabela_frame.winfo_children()[1:]:
            widget.destroy()

        if not self.resultados_atuais:
            aviso = ctk.CTkLabel(self.tabela_frame, text=mensagem_vazia, font=("Arial", 13), text_color="gray")
            aviso.pack(pady=20)
            return

        for i, produto in enumerate(self.resultados_atuais):
            id_prod, cod_ean, nome, preco, estoque = produto
            cor_linha = "#333333" if i % 2 == 0 else "transparent"

            row_frame = ctk.CTkFrame(self.tabela_frame, fg_color=cor_linha, corner_radius=0, cursor="hand2")
            row_frame.pack(fill="x", pady=0)

            dados_linha = [
                str(id_prod),
                str(cod_ean or "-"),
                str(nome).upper(),
                f"R$ {preco:.2f}".replace('.', ','),
                str(estoque)
            ]

            widgets_linha = [row_frame]
            for col, texto in enumerate(dados_linha):
                lbl = ctk.CTkLabel(row_frame, text=texto, font=("Arial", 13), text_color="white", anchor="center")
                lbl.grid(row=0, column=col, sticky="nsew", pady=8)
                row_frame.grid_columnconfigure(col, weight=self.table_weights[col], uniform="col_pesquisa")
                widgets_linha.append(lbl)

            # Vincula o duplo clique em toda a linha (frame + labels) à seleção do produto
            for widget in widgets_linha:
                widget.bind("<Double-Button-1>", lambda e, p=produto: self.selecionar_produto(p))

    def selecionar_produto(self, produto):
        """Devolve o produto escolhido para o MainPDV e fecha o modal."""
        self.ao_selecionar(produto)
        self.destroy()
