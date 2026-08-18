import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from utils.compras_service import criar_pedido_compra
from utils.fornec_service import buscar_fornecedores_db
from utils.product_service import buscar_produtos_db
from utils.financeiro_service import formatar_moeda_br


class ModalPedidoCompra(ctk.CTkToplevel):
    """
    Modal de criação de um novo Pedido de Compra. O operador monta a lista de itens
    (produto + quantidade + custo unitário) antes de confirmar; o valor total do
    pedido é calculado automaticamente (soma de quantidade × custo de cada item) e
    vira a conta a pagar gerada no Financeiro assim que o pedido é criado.
    """
    def __init__(self, master, ao_salvar):
        super().__init__(master)

        self.ao_salvar = ao_salvar
        self.itens_pedido = []  # cada item: {id_produto, nome_produto, quantidade, custo_unitario}
        self.mapa_produtos = {}  # nome -> id_produto, só produtos ativos

        self.title("Novo Pedido de Compra")
        self.geometry("720x680")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")

        self.transient(master)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="NOVO PEDIDO DE COMPRA", font=("Arial", 20, "bold"), text_color="#3498db").pack(pady=(20, 15))

        # --- FORNECEDOR E VENCIMENTO DO PAGAMENTO (lado a lado) ---
        topo_frame = ctk.CTkFrame(self, fg_color="transparent")
        topo_frame.pack(fill="x", padx=30, pady=(0, 12))

        col_fornec = ctk.CTkFrame(topo_frame, fg_color="transparent")
        col_fornec.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(col_fornec, text="FORNECEDOR:", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w")

        self.mapa_fornecedores = {}
        for fornecedor in buscar_fornecedores_db():
            f_id, f_nome = fornecedor[0], fornecedor[1]
            self.mapa_fornecedores[f_nome] = f_id

        nomes_fornecedores = list(self.mapa_fornecedores.keys()) or ["Nenhum fornecedor cadastrado"]
        self.fornecedor_var = ctk.StringVar(value=nomes_fornecedores[0])
        self.menu_fornecedor = ctk.CTkOptionMenu(col_fornec, values=nomes_fornecedores, variable=self.fornecedor_var, height=38)
        self.menu_fornecedor.pack(fill="x", pady=(2, 0))

        col_venc = ctk.CTkFrame(topo_frame, fg_color="transparent")
        col_venc.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(col_venc, text="VENCIMENTO DO PAGAMENTO:", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w")
        self.entry_vencimento = ctk.CTkEntry(col_venc, height=38, fg_color="#2b2b2b", placeholder_text="dd/mm/aaaa")
        self.entry_vencimento.pack(fill="x", pady=(2, 0))

        # --- ADICIONAR ITEM AO PEDIDO ---
        ctk.CTkLabel(self, text="ADICIONAR ITEM:", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30, pady=(5, 0))

        item_frame = ctk.CTkFrame(self, fg_color="transparent")
        item_frame.pack(fill="x", padx=30, pady=(2, 10))

        self.mapa_produtos = {}
        for produto in buscar_produtos_db(mostrar_tudo=0):
            p_id, p_ean, p_nome = produto[0], produto[1], produto[2]
            self.mapa_produtos[p_nome] = p_id

        nomes_produtos = list(self.mapa_produtos.keys()) or ["Nenhum produto cadastrado"]
        self.produto_var = ctk.StringVar(value=nomes_produtos[0])
        self.menu_produto = ctk.CTkOptionMenu(item_frame, values=nomes_produtos, variable=self.produto_var, width=250)
        self.menu_produto.pack(side="left", padx=(0, 5))

        self.entry_quantidade = ctk.CTkEntry(item_frame, width=90, fg_color="#2b2b2b", placeholder_text="Qtd.")
        self.entry_quantidade.pack(side="left", padx=5)

        self.entry_custo = ctk.CTkEntry(item_frame, width=100, fg_color="#2b2b2b", placeholder_text="Custo Unit.")
        self.entry_custo.pack(side="left", padx=5)

        btn_adicionar = ctk.CTkButton(item_frame, text="+ Adicionar", width=100, fg_color="#27ae60", hover_color="#1e8449", command=self.adicionar_item)
        btn_adicionar.pack(side="left", padx=(5, 0))

        # --- LISTA DE ITENS JÁ ADICIONADOS ---
        self.lista_frame = ctk.CTkScrollableFrame(self, fg_color="#242424", corner_radius=10, height=220)
        self.lista_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        # --- OBSERVAÇÃO ---
        self.entry_observacao = ctk.CTkEntry(self, height=38, fg_color="#2b2b2b", placeholder_text="Observação (opcional)")
        self.entry_observacao.pack(fill="x", padx=30, pady=(0, 5))

        # --- TOTAL E BOTÃO FINAL ---
        self.lbl_total = ctk.CTkLabel(self, text="TOTAL DO PEDIDO: R$ 0,00", font=("Arial", 16, "bold"), text_color="#f39c12")
        self.lbl_total.pack(pady=(5, 10))

        self.btn_confirmar = ctk.CTkButton(
            self, text="CONFIRMAR PEDIDO DE COMPRA",
            command=self.salvar_pedido,
            fg_color="#3498db", hover_color="#2980b9",
            height=45, font=("Arial", 14, "bold")
        )
        self.btn_confirmar.pack(fill="x", padx=30, pady=(0, 20))

        self.bind("<Escape>", lambda e: self.destroy())
        self.renderizar_itens()

    def adicionar_item(self):
        nome_produto = self.produto_var.get()
        id_produto = self.mapa_produtos.get(nome_produto)

        if not id_produto:
            messagebox.showwarning("Atenção", "Nenhum produto válido selecionado.")
            return

        try:
            quantidade = int(self.entry_quantidade.get().strip())
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe uma quantidade válida (número inteiro maior que zero).")
            return

        try:
            custo_unitario = float(self.entry_custo.get().strip().replace(',', '.'))
            if custo_unitario < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um custo unitário válido.")
            return

        self.itens_pedido.append({
            "id_produto": id_produto,
            "nome_produto": nome_produto,
            "quantidade": quantidade,
            "custo_unitario": custo_unitario
        })

        self.entry_quantidade.delete(0, 'end')
        self.entry_custo.delete(0, 'end')
        self.renderizar_itens()

    def remover_item(self, indice):
        del self.itens_pedido[indice]
        self.renderizar_itens()

    def renderizar_itens(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        if not self.itens_pedido:
            ctk.CTkLabel(self.lista_frame, text="Nenhum item adicionado ainda.", text_color="gray").pack(pady=20)
        else:
            for i, item in enumerate(self.itens_pedido):
                subtotal = item["quantidade"] * item["custo_unitario"]

                linha = ctk.CTkFrame(self.lista_frame, fg_color="#2b2b2b" if i % 2 == 0 else "transparent")
                linha.pack(fill="x", pady=2)

                texto = f"{item['nome_produto']}  —  {item['quantidade']} un. × {formatar_moeda_br(item['custo_unitario'])} = {formatar_moeda_br(subtotal)}"
                ctk.CTkLabel(linha, text=texto, anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=6)

                btn_remover = ctk.CTkButton(
                    linha, text="✕", width=28, height=24, font=("Arial", 11, "bold"),
                    fg_color="transparent", border_width=1, border_color="#e74c3c", text_color="#e74c3c",
                    hover_color="#333333",
                    command=lambda idx=i: self.remover_item(idx)
                )
                btn_remover.pack(side="right", padx=10)

        total = sum(item["quantidade"] * item["custo_unitario"] for item in self.itens_pedido)
        self.lbl_total.configure(text=f"TOTAL DO PEDIDO: {formatar_moeda_br(total)}")

    def salvar_pedido(self):
        nome_fornecedor = self.fornecedor_var.get()
        id_fornecedor = self.mapa_fornecedores.get(nome_fornecedor)

        if not id_fornecedor:
            messagebox.showwarning("Atenção", "Selecione um fornecedor válido.")
            return

        if not self.itens_pedido:
            messagebox.showwarning("Atenção", "Adicione ao menos um item ao pedido.")
            return

        vencimento_texto = self.entry_vencimento.get().strip()
        try:
            vencimento_iso = datetime.strptime(vencimento_texto, "%d/%m/%Y").date().isoformat()
        except ValueError:
            messagebox.showwarning("Atenção", "Informe o vencimento do pagamento no formato dd/mm/aaaa.")
            return

        observacao = self.entry_observacao.get().strip()

        if not messagebox.askyesno(
            "Confirmar Pedido",
            f"Confirmar pedido de compra para {nome_fornecedor}?\n"
            f"Isso vai gerar automaticamente uma conta a pagar no Financeiro."
        ):
            return

        sucesso, resultado = criar_pedido_compra(id_fornecedor, self.itens_pedido, vencimento_iso, observacao)

        if sucesso:
            messagebox.showinfo("Sucesso", f"Pedido de compra #{resultado} criado com sucesso!")
            if self.ao_salvar:
                self.ao_salvar()
            self.destroy()
        else:
            messagebox.showerror("Erro", f"Não foi possível criar o pedido: {resultado}")
