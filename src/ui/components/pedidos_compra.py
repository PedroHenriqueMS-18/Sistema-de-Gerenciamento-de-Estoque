import customtkinter as ctk
from tkinter import messagebox
from utils.compras_service import buscar_pedidos_compra, cancelar_pedido_compra
from utils.financeiro_service import formatar_moeda_br, formatar_data_exibir


class PedidosCompra(ctk.CTkFrame):
    """
    Tela de Pedidos de Compra (reposição de estoque). Acessível tanto por
    supervisores quanto por operadores (Níveis 1 e 2), pela sidebar da
    MainWindow. Fluxo: PENDENTE -> RECEBIDO (com conferência de quantidade),
    ou CANCELADO a qualquer momento.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(
            self, text="Pedidos de Compra",
            font=ctk.CTkFont(family="Arial", size=32, weight="bold")
        ).pack(anchor="w", padx=30, pady=(10, 20))

        # --- FILTROS E AÇÕES ---
        filtro_frame = ctk.CTkFrame(self, fg_color="transparent")
        filtro_frame.pack(fill="x", padx=30, pady=(0, 10))

        self.status_var = ctk.StringVar(value="TODOS")
        menu_status = ctk.CTkOptionMenu(
            filtro_frame,
            values=["TODOS", "PENDENTE", "RECEBIDO", "CANCELADO"],
            variable=self.status_var,
            width=140,
            command=lambda e: self.carregar_pedidos()
        )
        menu_status.pack(side="left", padx=(0, 10))

        self.entry_busca = ctk.CTkEntry(filtro_frame, placeholder_text="Pesquisar por fornecedor...", width=280)
        self.entry_busca.pack(side="left", padx=(0, 10))
        self.entry_busca.bind("<Return>", lambda e: self.carregar_pedidos())

        btn_buscar = ctk.CTkButton(filtro_frame, text="Buscar", width=90, command=self.carregar_pedidos)
        btn_buscar.pack(side="left")

        btn_novo = ctk.CTkButton(
            filtro_frame, text="+ Novo Pedido de Compra",
            fg_color="#27ae60", hover_color="#1e8449",
            command=self.abrir_novo_pedido
        )
        btn_novo.pack(side="right")

        # --- TABELA ---
        self.tabela_frame = ctk.CTkScrollableFrame(self, fg_color="#242424", corner_radius=15)
        self.tabela_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self.carregar_pedidos()

    def carregar_pedidos(self):
        status_filtro = self.status_var.get()
        termo_busca = self.entry_busca.get().strip()
        pedidos = buscar_pedidos_compra(status_filtro, termo_busca)

        for widget in self.tabela_frame.winfo_children():
            widget.destroy()

        headers = ["Fornecedor", "Valor Total", "Data", "Status", "Ação"]
        pesos = [3, 1, 1, 1, 2]
        for idx, peso in enumerate(pesos):
            self.tabela_frame.grid_columnconfigure(idx, weight=peso, uniform="col_compras")

        for i, col in enumerate(headers):
            ctk.CTkLabel(self.tabela_frame, text=col, font=("Arial", 13, "bold"), text_color="gray").grid(row=0, column=i, pady=10, sticky="nsew")

        if not pedidos:
            ctk.CTkLabel(self.tabela_frame, text="Nenhum pedido de compra encontrado.", text_color="gray")\
                .grid(row=1, column=0, columnspan=len(headers), pady=20)
            return

        cores_status = {
            "PENDENTE": "#f39c12",
            "RECEBIDO": "#2ecc71",
            "CANCELADO": "#7f8c8d"
        }

        for i, (id_pedido, nome_fornecedor, status, valor_total, valor_recebido, criado_em) in enumerate(pedidos):
            row_idx = i + 1
            cor_fundo = "#2b2b2b" if row_idx % 2 == 0 else "transparent"

            row_frame = ctk.CTkFrame(self.tabela_frame, fg_color=cor_fundo, corner_radius=5)
            row_frame.grid(row=row_idx, column=0, columnspan=len(headers), sticky="ew", pady=2)
            for idx, peso in enumerate(pesos):
                row_frame.grid_columnconfigure(idx, weight=peso, uniform="col_compras")

            ctk.CTkLabel(row_frame, text=f"#{id_pedido} - {nome_fornecedor}", anchor="w", font=("Arial", 12, "bold"))\
                .grid(row=0, column=0, sticky="ew", padx=10, pady=8)

            if valor_recebido is not None and abs(valor_recebido - valor_total) > 0.004:
                texto_valor = f"{formatar_moeda_br(valor_recebido)} (pedido: {formatar_moeda_br(valor_total)})"
            else:
                texto_valor = formatar_moeda_br(valor_total)
            ctk.CTkLabel(row_frame, text=texto_valor, font=("Arial", 11)).grid(row=0, column=1, sticky="ew", pady=8)
            ctk.CTkLabel(row_frame, text=formatar_data_exibir(str(criado_em)[:10])).grid(row=0, column=2, sticky="ew", pady=8)
            ctk.CTkLabel(row_frame, text=status, text_color=cores_status.get(status, "white"), font=("Arial", 12, "bold"))\
                .grid(row=0, column=3, sticky="ew", pady=8)

            acoes_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            acoes_frame.grid(row=0, column=4, pady=4, padx=5)

            if status == "PENDENTE":
                btn_receber = ctk.CTkButton(
                    acoes_frame, text="Confirmar Recebimento", width=150, height=26, font=("Arial", 11, "bold"),
                    fg_color="#27ae60", hover_color="#1e8449",
                    command=lambda pid=id_pedido, forn=nome_fornecedor: self.abrir_recebimento(pid, forn)
                )
                btn_receber.pack(side="left", padx=(0, 5))

            if status in ("PENDENTE", "RECEBIDO"):
                btn_cancelar = ctk.CTkButton(
                    acoes_frame, text="Cancelar", width=70, height=26, font=("Arial", 11, "bold"),
                    fg_color="transparent", border_width=1, border_color="#e74c3c", text_color="#e74c3c",
                    hover_color="#333333",
                    command=lambda pid=id_pedido: self.cancelar_pedido(pid)
                )
                btn_cancelar.pack(side="left")

    def abrir_novo_pedido(self):
        from ui.components.modal_pedido_compra import ModalPedidoCompra
        ModalPedidoCompra(master=self.winfo_toplevel(), ao_salvar=self.carregar_pedidos)

    def abrir_recebimento(self, id_pedido, nome_fornecedor):
        from ui.components.modal_confirmar_recebimento import ModalConfirmarRecebimento
        ModalConfirmarRecebimento(
            master=self.winfo_toplevel(),
            id_pedido=id_pedido,
            nome_fornecedor=nome_fornecedor,
            ao_confirmar=self.carregar_pedidos
        )

    def cancelar_pedido(self, id_pedido):
        if not messagebox.askyesno(
            "Cancelar Pedido",
            "Cancelar este pedido de compra?\n"
            "Se ele já tinha sido recebido, o estoque dado como entrada será estornado, "
            "e a conta a pagar vinculada também será cancelada."
        ):
            return

        sucesso, resultado = cancelar_pedido_compra(id_pedido)

        if sucesso:
            self.carregar_pedidos()
        else:
            messagebox.showerror("Erro", f"Não foi possível cancelar o pedido: {resultado}")
