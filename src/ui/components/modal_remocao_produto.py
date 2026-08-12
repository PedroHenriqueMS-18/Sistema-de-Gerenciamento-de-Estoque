import customtkinter as ctk


class ModalRemocaoProduto(ctk.CTkToplevel):
    """
    Modal de remoção de produtos da venda atual do PDV (atalho F2).
    Lista todos os itens já lançados na venda em andamento e permite
    removê-los com um duplo clique, reaproveitando a mesma confirmação
    e o mesmo recálculo de totais já usados na tela principal
    (MainPDV.excluir_item_venda).
    """
    def __init__(self, master, callback_remover):
        super().__init__(master)

        self.master_pdv = master  # Referência ao MainPDV -> fonte viva de 'itens_venda'
        self.callback_remover = callback_remover  # MainPDV.excluir_item_venda

        # Configurações da Janela
        self.title("Remover Produto da Venda (F2)")
        self.geometry("780x560")
        self.configure(fg_color="#1a1a1a")

        # Garante que o usuário interaja apenas com essa janela (Modal)
        self.transient(master)
        self.grab_set()

        self.table_weights = [1, 2, 4, 1, 1, 1]

        self.setup_ui()
        self.configurar_binds()
        self.renderizar_itens()

    def setup_ui(self):
        ctk.CTkLabel(
            self, text="REMOVER PRODUTO DA VENDA",
            font=("Arial", 20, "bold"), text_color="#e74c3c"
        ).pack(pady=(15, 10))

        # --- TABELA DE ITENS DA VENDA ATUAL ---
        self.tabela_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.tabela_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.render_cabecalho()

        # --- RODAPÉ DE ORIENTAÇÃO ---
        self.lbl_dica = ctk.CTkLabel(
            self,
            text="Dê um duplo clique no produto para removê-lo da venda atual. (ESC fecha a janela)",
            font=("Arial", 11),
            text_color="gray"
        )
        self.lbl_dica.pack(pady=(0, 15))

    def render_cabecalho(self):
        headers = ["ÍT.", "EAN", "PRODUTO", "QTD", "VL. UNIT.", "SUBTOTAL"]

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
            header_row.grid_columnconfigure(i, weight=self.table_weights[i], uniform="col_remocao")

    def configurar_binds(self):
        self.bind("<Escape>", lambda e: self.destroy())

    def renderizar_itens(self):
        # Remove apenas as linhas de item, preservando o cabeçalho fixo (primeiro filho)
        for widget in self.tabela_frame.winfo_children()[1:]:
            widget.destroy()

        # Lê direto da lista viva do MainPDV, garantindo que a remoção reflita na hora
        itens_atuais = self.master_pdv.itens_venda

        if not itens_atuais:
            aviso = ctk.CTkLabel(
                self.tabela_frame, text="Não há produtos na venda atual.",
                font=("Arial", 13), text_color="gray"
            )
            aviso.pack(pady=20)
            return

        for i, item in enumerate(itens_atuais):
            cor_linha = "#333333" if i % 2 == 0 else "transparent"

            row_frame = ctk.CTkFrame(self.tabela_frame, fg_color=cor_linha, corner_radius=0, cursor="hand2")
            row_frame.pack(fill="x", pady=0)

            dados_linha = [
                f"{i + 1:03d}",
                str(item['ean']),
                str(item['nome']).upper(),
                f"{item['qtd']:.3f}".replace('.', ','),
                f"{item['preco']:.2f}".replace('.', ','),
                f"{item['subtotal']:.2f}".replace('.', ',')
            ]

            widgets_linha = [row_frame]
            for col, texto in enumerate(dados_linha):
                lbl = ctk.CTkLabel(row_frame, text=texto, font=("Arial", 13), text_color="white", anchor="center")
                lbl.grid(row=0, column=col, sticky="nsew", pady=8)
                row_frame.grid_columnconfigure(col, weight=self.table_weights[col], uniform="col_remocao")
                widgets_linha.append(lbl)

            # Vincula o duplo clique em toda a linha (frame + labels) à remoção do item
            for widget in widgets_linha:
                widget.bind("<Double-Button-1>", lambda e, idx=i: self.remover_item(idx))

    def remover_item(self, indice):
        """Aciona a remoção real (com confirmação) e atualiza a lista exibida no modal."""
        self.callback_remover(indice)
        self.renderizar_itens()

        # Se o usuário removeu o último item, fecha a janela automaticamente
        if not self.master_pdv.itens_venda:
            self.destroy()
