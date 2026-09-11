import customtkinter as ctk
from tkinter import messagebox
from datetime import date, datetime, timedelta
from utils.financeiro_service import formatar_moeda_br, formatar_data_exibir
from utils.relatorios_service import (
    relatorio_vendas_periodo,
    relatorio_compras_periodo,
    relatorio_divergencia_compras,
    relatorio_dre_simplificado
)

FORMAS_PAGAMENTO = {1: "Dinheiro", 2: "Cartão Crédito", 3: "Cartão Débito", 4: "PIX", 5: "Cheque"}


class SeletorPeriodo(ctk.CTkFrame):
    """
    Componente reutilizável de seleção de período, usado em todas as abas de
    Relatórios: opções rápidas (Hoje, Ontem, Últimos 7 dias, Este Mês, Mês
    Passado) ou um intervalo Personalizado com datas digitadas. Chama
    'ao_aplicar(data_inicio_iso, data_fim_iso)' sempre que o período muda.
    """
    def __init__(self, master, ao_aplicar):
        super().__init__(master, fg_color="transparent")
        self.ao_aplicar = ao_aplicar

        self.opcao_var = ctk.StringVar(value="Hoje")
        self.menu_opcao = ctk.CTkOptionMenu(
            self, values=["Hoje", "Ontem", "Últimos 7 dias", "Este Mês", "Mês Passado", "Personalizado"],
            variable=self.opcao_var, width=160, command=self.ao_mudar_opcao
        )
        self.menu_opcao.pack(side="left", padx=(0, 10))

        self.entry_inicio = ctk.CTkEntry(self, placeholder_text="dd/mm/aaaa", width=110, fg_color="#2b2b2b", state="disabled")
        self.entry_inicio.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(self, text="até").pack(side="left", padx=5)

        self.entry_fim = ctk.CTkEntry(self, placeholder_text="dd/mm/aaaa", width=110, fg_color="#2b2b2b", state="disabled")
        self.entry_fim.pack(side="left", padx=(5, 10))

        self.btn_aplicar = ctk.CTkButton(self, text="Aplicar", width=90, command=self.aplicar)
        self.btn_aplicar.pack(side="left")

    def ao_mudar_opcao(self, valor):
        estado = "normal" if valor == "Personalizado" else "disabled"
        self.entry_inicio.configure(state=estado)
        self.entry_fim.configure(state=estado)
        if valor != "Personalizado":
            self.aplicar()

    def calcular_datas(self):
        hoje = date.today()
        opcao = self.opcao_var.get()

        if opcao == "Hoje":
            return hoje, hoje
        elif opcao == "Ontem":
            ontem = hoje - timedelta(days=1)
            return ontem, ontem
        elif opcao == "Últimos 7 dias":
            return hoje - timedelta(days=6), hoje
        elif opcao == "Este Mês":
            return hoje.replace(day=1), hoje
        elif opcao == "Mês Passado":
            primeiro_dia_mes_atual = hoje.replace(day=1)
            ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)
            primeiro_dia_mes_passado = ultimo_dia_mes_passado.replace(day=1)
            return primeiro_dia_mes_passado, ultimo_dia_mes_passado
        else:  # Personalizado
            try:
                data_inicio = datetime.strptime(self.entry_inicio.get().strip(), "%d/%m/%Y").date()
                data_fim = datetime.strptime(self.entry_fim.get().strip(), "%d/%m/%Y").date()
                return data_inicio, data_fim
            except ValueError:
                messagebox.showwarning("Atenção", "Informe as duas datas no formato dd/mm/aaaa.")
                return None, None

    def aplicar(self):
        data_inicio, data_fim = self.calcular_datas()
        if data_inicio is None:
            return
        self.ao_aplicar(data_inicio.isoformat(), data_fim.isoformat())


class Relatorios(ctk.CTkFrame):
    """
    Tela de Relatórios. Acessível por Nível 1 e Nível 2 (mesmo público de
    Compras). Quatro abas: Vendas por Período, Compras por Período,
    Divergência de Compras e DRE Simplificado. Só leitura — nenhuma tabela
    nova no banco, tudo cruzado a partir do que já existe.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(
            self, text="Relatórios",
            font=ctk.CTkFont(family="Arial", size=32, weight="bold")
        ).pack(anchor="w", padx=30, pady=(10, 20))

        self.tabview = ctk.CTkTabview(self, fg_color="#1a1a1a")
        self.tabview.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self.montar_aba_vendas(self.tabview.add("Vendas"))
        self.montar_aba_compras(self.tabview.add("Compras"))
        self.montar_aba_divergencia(self.tabview.add("Divergência de Compras"))
        self.montar_aba_dre(self.tabview.add("DRE Simplificado"))

    def criar_card(self, parent, titulo, cor):
        card = ctk.CTkFrame(parent, fg_color="#1a1c1e", height=95, corner_radius=15, border_width=1, border_color="#313437")
        card.pack(side="left", fill="x", expand=True, padx=5)
        card.pack_propagate(False)

        ctk.CTkLabel(card, text=titulo, font=("Arial", 12, "bold"), text_color="gray").pack(pady=(15, 5), padx=15, anchor="w")
        label_valor = ctk.CTkLabel(card, text="—", font=("Arial", 20, "bold"), text_color=cor)
        label_valor.pack(pady=(0, 15), padx=15, anchor="w")
        return label_valor

    def montar_tabela_generica(self, tabela_frame, headers, pesos):
        for widget in tabela_frame.winfo_children():
            widget.destroy()
        for idx, peso in enumerate(pesos):
            tabela_frame.grid_columnconfigure(idx, weight=peso, uniform="col_rel")
        for i, col in enumerate(headers):
            ctk.CTkLabel(tabela_frame, text=col, font=("Arial", 12, "bold"), text_color="gray").grid(row=0, column=i, pady=8, sticky="nsew")

    def adicionar_linha_tabela(self, tabela_frame, row_idx, valores, pesos, cor_destaque=None, col_destaque=None):
        cor_fundo = "#2b2b2b" if row_idx % 2 == 0 else "transparent"
        row_frame = ctk.CTkFrame(tabela_frame, fg_color=cor_fundo, corner_radius=5)
        row_frame.grid(row=row_idx, column=0, columnspan=len(valores), sticky="ew", pady=1)
        for idx, peso in enumerate(pesos):
            row_frame.grid_columnconfigure(idx, weight=peso, uniform="col_rel")
        for col, texto in enumerate(valores):
            cor = cor_destaque if (col_destaque is not None and col == col_destaque and cor_destaque) else "white"
            ctk.CTkLabel(row_frame, text=str(texto), font=("Arial", 12), text_color=cor).grid(row=0, column=col, sticky="ew", padx=6, pady=6)

    # ============================== ABA 1: VENDAS ==============================
    def montar_aba_vendas(self, container):
        SeletorPeriodo(container, ao_aplicar=self.carregar_vendas).pack(anchor="w", padx=10, pady=(15, 10))

        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.card_vendas_total = self.criar_card(cards_frame, "Total Vendido", "#27ae60")
        self.card_vendas_qtd = self.criar_card(cards_frame, "Nº de Vendas", "#3498db")
        self.card_vendas_ticket = self.criar_card(cards_frame, "Ticket Médio", "#f39c12")

        self.lbl_vendas_formas = ctk.CTkLabel(container, text="", font=("Arial", 12), text_color="gray", justify="left")
        self.lbl_vendas_formas.pack(anchor="w", padx=10, pady=(0, 10))

        self.tabela_vendas = ctk.CTkScrollableFrame(container, fg_color="#242424", corner_radius=15)
        self.tabela_vendas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.pesos_vendas = [1, 2, 1, 1, 1, 1]
        self.carregar_vendas(date.today().isoformat(), date.today().isoformat())

    def carregar_vendas(self, data_inicio, data_fim):
        dados = relatorio_vendas_periodo(data_inicio, data_fim)
        if dados is None:
            messagebox.showerror("Erro", "Não foi possível carregar o relatório de vendas.")
            return

        self.card_vendas_total.configure(text=formatar_moeda_br(dados["total_vendido"]))
        self.card_vendas_qtd.configure(text=str(dados["num_vendas"]))
        self.card_vendas_ticket.configure(text=formatar_moeda_br(dados["ticket_medio"]))

        partes_forma = [
            f"{FORMAS_PAGAMENTO.get(forma, 'Outro')}: {formatar_moeda_br(valor)}"
            for forma, valor in dados["totais_forma"].items()
        ]
        self.lbl_vendas_formas.configure(text="Por forma de pagamento — " + " | ".join(partes_forma) if partes_forma else "Nenhuma venda no período.")

        headers = ["Nº VENDA", "OPERADOR", "VALOR", "DATA", "HORA", "FORMA"]
        self.montar_tabela_generica(self.tabela_vendas, headers, self.pesos_vendas)

        if not dados["vendas"]:
            ctk.CTkLabel(self.tabela_vendas, text="Nenhuma venda no período.", text_color="gray").grid(row=1, column=0, columnspan=len(headers), pady=20)
            return

        for i, (id_venda, operador, valor, data_venda, hora_venda, id_forma) in enumerate(dados["vendas"]):
            self.adicionar_linha_tabela(self.tabela_vendas, i + 1, [
                f"#{id_venda}", operador, formatar_moeda_br(valor),
                formatar_data_exibir(str(data_venda)[:10]), str(hora_venda)[:8],
                FORMAS_PAGAMENTO.get(id_forma, "—")
            ], self.pesos_vendas)

    # ============================== ABA 2: COMPRAS ==============================
    def montar_aba_compras(self, container):
        SeletorPeriodo(container, ao_aplicar=self.carregar_compras).pack(anchor="w", padx=10, pady=(15, 10))

        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.card_compras_pedido = self.criar_card(cards_frame, "Total Pedido", "#e74c3c")
        self.card_compras_recebido = self.criar_card(cards_frame, "Total Recebido", "#27ae60")
        self.card_compras_status = self.criar_card(cards_frame, "Pedidos (Pend./Receb./Cancel.)", "#3498db")

        self.tabela_compras = ctk.CTkScrollableFrame(container, fg_color="#242424", corner_radius=15)
        self.tabela_compras.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.pesos_compras = [1, 2, 1, 1, 1, 1]
        self.carregar_compras(date.today().isoformat(), date.today().isoformat())

    def carregar_compras(self, data_inicio, data_fim):
        dados = relatorio_compras_periodo(data_inicio, data_fim)
        if dados is None:
            messagebox.showerror("Erro", "Não foi possível carregar o relatório de compras.")
            return

        self.card_compras_pedido.configure(text=formatar_moeda_br(dados["total_pedido"]))
        self.card_compras_recebido.configure(text=formatar_moeda_br(dados["total_recebido"]))
        c = dados["contagem_status"]
        self.card_compras_status.configure(text=f"{c['PENDENTE']} / {c['RECEBIDO']} / {c['CANCELADO']}")

        headers = ["PEDIDO", "FORNECEDOR", "STATUS", "VALOR PEDIDO", "VALOR RECEBIDO", "DATA"]
        self.montar_tabela_generica(self.tabela_compras, headers, self.pesos_compras)

        if not dados["pedidos"]:
            ctk.CTkLabel(self.tabela_compras, text="Nenhum pedido no período.", text_color="gray").grid(row=1, column=0, columnspan=len(headers), pady=20)
            return

        for i, (id_pedido, fornecedor, status, valor_pedido, valor_recebido, criado_em) in enumerate(dados["pedidos"]):
            self.adicionar_linha_tabela(self.tabela_compras, i + 1, [
                f"#{id_pedido}", fornecedor, status, formatar_moeda_br(valor_pedido),
                formatar_moeda_br(valor_recebido) if valor_recebido is not None else "—",
                formatar_data_exibir(str(criado_em)[:10])
            ], self.pesos_compras)

    # ======================= ABA 3: DIVERGÊNCIA DE COMPRAS =======================
    def montar_aba_divergencia(self, container):
        SeletorPeriodo(container, ao_aplicar=self.carregar_divergencia).pack(anchor="w", padx=10, pady=(15, 10))

        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.card_div_faltante = self.criar_card(cards_frame, "Unidades Faltantes", "#e74c3c")
        self.card_div_excedente = self.criar_card(cards_frame, "Unidades Excedentes", "#f39c12")

        self.tabela_divergencia = ctk.CTkScrollableFrame(container, fg_color="#242424", corner_radius=15)
        self.tabela_divergencia.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.carregar_divergencia(date.today().isoformat(), date.today().isoformat())

    def carregar_divergencia(self, data_inicio, data_fim):
        dados = relatorio_divergencia_compras(data_inicio, data_fim)
        if dados is None:
            messagebox.showerror("Erro", "Não foi possível carregar o relatório de divergência.")
            return

        self.card_div_faltante.configure(text=str(dados["total_faltante"]))
        self.card_div_excedente.configure(text=str(dados["total_excedente"]))

        for widget in self.tabela_divergencia.winfo_children():
            widget.destroy()

        if not dados["pedidos"]:
            ctk.CTkLabel(self.tabela_divergencia, text="Nenhuma divergência de recebimento no período.", text_color="gray").pack(pady=20)
            return

        for pedido in dados["pedidos"]:
            titulo = f"Pedido #{pedido['id_pedido']} — {pedido['nome_fornecedor']} ({formatar_data_exibir(str(pedido['criado_em'])[:10])})"
            ctk.CTkLabel(self.tabela_divergencia, text=titulo, font=("Arial", 13, "bold"), text_color="#3498db")\
                .pack(anchor="w", padx=10, pady=(12, 4))

            for nome_produto, qtd_pedida, qtd_recebida, diferenca in pedido["itens"]:
                if diferenca > 0:
                    texto_diff, cor = f"faltaram {diferenca}", "#e74c3c"
                else:
                    texto_diff, cor = f"excedente de {abs(diferenca)}", "#f39c12"
                linha = f"  • {nome_produto}: pedido {qtd_pedida}, recebido {qtd_recebida} ({texto_diff})"
                ctk.CTkLabel(self.tabela_divergencia, text=linha, font=("Arial", 12), text_color=cor).pack(anchor="w", padx=15)

    # ========================== ABA 4: DRE SIMPLIFICADO ==========================
    def montar_aba_dre(self, container):
        SeletorPeriodo(container, ao_aplicar=self.carregar_dre).pack(anchor="w", padx=10, pady=(15, 10))

        ctk.CTkLabel(
            container,
            text="⚠️ O Custo da Mercadoria Vendida (CMV) usa o custo ATUAL de cada produto — não o custo da\n"
                 "época da venda (que o sistema não guarda). Para o período atual isso é uma boa aproximação;\n"
                 "para meses muito distantes no tempo, pode não refletir o custo real daquele momento.",
            font=("Arial", 11), text_color="#f39c12", justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 15))

        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.card_dre_receita = self.criar_card(cards_frame, "Receita", "#3498db")
        self.card_dre_cmv = self.criar_card(cards_frame, "CMV (aprox.)", "#e74c3c")
        self.card_dre_despesas = self.criar_card(cards_frame, "Despesas Pagas", "#e74c3c")
        self.card_dre_lucro = self.criar_card(cards_frame, "Lucro", "#27ae60")

        self.carregar_dre(date.today().isoformat(), date.today().isoformat())

    def carregar_dre(self, data_inicio, data_fim):
        dados = relatorio_dre_simplificado(data_inicio, data_fim)
        if dados is None:
            messagebox.showerror("Erro", "Não foi possível calcular o DRE simplificado.")
            return

        self.card_dre_receita.configure(text=formatar_moeda_br(dados["receita"]))
        self.card_dre_cmv.configure(text=formatar_moeda_br(dados["cmv"]))
        self.card_dre_despesas.configure(text=formatar_moeda_br(dados["despesas"]))

        cor_lucro = "#27ae60" if dados["lucro"] >= 0 else "#e74c3c"
        self.card_dre_lucro.configure(text=formatar_moeda_br(dados["lucro"]), text_color=cor_lucro)
