import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from utils.financeiro_service import (
    formatar_moeda_br,
    formatar_data_exibir,
    buscar_titulos_financeiros,
    calcular_totais_financeiros,
    marcar_titulo_como_pago,
    cancelar_titulo_financeiro
)


class Financeiro(ctk.CTkFrame):
    """
    Tela de Financeiro (Contas a Pagar / Contas a Receber). Acessível só para
    supervisores (Nível 1), pela sidebar da MainWindow — totalmente fora do
    fluxo do PDV. Lançamento manual de títulos, sem pagamento parcial: cada
    título só tem dois destinos possíveis, PAGO (integral) ou CANCELADO.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.refs = {}  # guarda os widgets de cada aba (PAGAR / RECEBER) para recarregar depois
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(
            self, text="Financeiro",
            font=ctk.CTkFont(family="Arial", size=32, weight="bold")
        ).pack(anchor="w", padx=30, pady=(10, 20))

        self.tabview = ctk.CTkTabview(self, fg_color="#1a1a1a")
        self.tabview.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        aba_pagar = self.tabview.add("A Pagar")
        aba_receber = self.tabview.add("A Receber")

        self.montar_aba(aba_pagar, "PAGAR")
        self.montar_aba(aba_receber, "RECEBER")

    def montar_aba(self, container, tipo):
        cor_destaque = "#e74c3c" if tipo == "PAGAR" else "#27ae60"

        # --- CARDS DE RESUMO ---
        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=(15, 15))

        card_pendente = self.criar_card(cards_frame, "Pendente", cor_destaque)
        card_vencido = self.criar_card(cards_frame, "Vencido", "#e74c3c")
        card_pago = self.criar_card(cards_frame, "Pago Este Mês" if tipo == "PAGAR" else "Recebido Este Mês", "#3498db")

        # --- FILTROS E AÇÕES ---
        filtro_frame = ctk.CTkFrame(container, fg_color="transparent")
        filtro_frame.pack(fill="x", padx=10, pady=(0, 10))

        status_var = ctk.StringVar(value="TODOS")
        menu_status = ctk.CTkOptionMenu(
            filtro_frame,
            values=["TODOS", "PENDENTE", "PAGO", "CANCELADO"],
            variable=status_var,
            width=140,
            command=lambda e: self.carregar_titulos(tipo)
        )
        menu_status.pack(side="left", padx=(0, 10))

        entry_busca = ctk.CTkEntry(filtro_frame, placeholder_text="Pesquisar por descrição...", width=280)
        entry_busca.pack(side="left", padx=(0, 10))
        entry_busca.bind("<Return>", lambda e: self.carregar_titulos(tipo))

        btn_buscar = ctk.CTkButton(filtro_frame, text="Buscar", width=90, command=lambda: self.carregar_titulos(tipo))
        btn_buscar.pack(side="left")

        texto_botao_novo = "+ Nova Conta a Pagar" if tipo == "PAGAR" else "+ Nova Conta a Receber"
        btn_novo = ctk.CTkButton(
            filtro_frame, text=texto_botao_novo,
            fg_color="#27ae60", hover_color="#1e8449",
            command=lambda: self.abrir_novo_lancamento(tipo)
        )
        btn_novo.pack(side="right")

        # --- TABELA ---
        tabela_frame = ctk.CTkScrollableFrame(container, fg_color="#242424", corner_radius=15)
        tabela_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.refs[tipo] = {
            "status_var": status_var,
            "entry_busca": entry_busca,
            "tabela_frame": tabela_frame,
            "card_pendente": card_pendente,
            "card_vencido": card_vencido,
            "card_pago": card_pago,
        }

        self.carregar_titulos(tipo)

    def criar_card(self, parent, titulo, cor):
        card = ctk.CTkFrame(parent, fg_color="#1a1c1e", height=100, corner_radius=15, border_width=1, border_color="#313437")
        card.pack(side="left", fill="x", expand=True, padx=5)
        card.pack_propagate(False)

        ctk.CTkLabel(card, text=titulo, font=("Arial", 13, "bold"), text_color="gray").pack(pady=(15, 5), padx=20, anchor="w")
        label_valor = ctk.CTkLabel(card, text="R$ 0,00", font=("Arial", 22, "bold"), text_color=cor)
        label_valor.pack(pady=(0, 15), padx=20, anchor="w")
        return label_valor

    def carregar_titulos(self, tipo):
        refs = self.refs[tipo]

        # --- ATUALIZA OS CARDS DE RESUMO ---
        totais = calcular_totais_financeiros(tipo)
        refs["card_pendente"].configure(text=formatar_moeda_br(totais["total_pendente"]))
        refs["card_vencido"].configure(text=formatar_moeda_br(totais["total_vencido"]))
        refs["card_pago"].configure(text=formatar_moeda_br(totais["total_pago_mes"]))

        # --- RECARREGA A TABELA ---
        status_filtro = refs["status_var"].get()
        termo_busca = refs["entry_busca"].get().strip()
        titulos = buscar_titulos_financeiros(tipo, status_filtro, termo_busca)

        tabela_frame = refs["tabela_frame"]
        for widget in tabela_frame.winfo_children():
            widget.destroy()

        headers = ["Descrição", "Categoria", "Valor", "Vencimento", "Status", "Ação"]
        pesos = [3, 2, 1, 1, 1, 2]
        for idx, peso in enumerate(pesos):
            tabela_frame.grid_columnconfigure(idx, weight=peso, uniform="col_fin")

        for i, col in enumerate(headers):
            ctk.CTkLabel(tabela_frame, text=col, font=("Arial", 13, "bold"), text_color="gray").grid(row=0, column=i, pady=10, sticky="nsew")

        if not titulos:
            ctk.CTkLabel(tabela_frame, text="Nenhum lançamento encontrado.", text_color="gray")\
                .grid(row=1, column=0, columnspan=len(headers), pady=20)
            return

        hoje = datetime.now().date().isoformat()

        for i, (t_id, descricao, categoria, valor, vencimento, status, id_fornecedor) in enumerate(titulos):
            row_idx = i + 1

            if status == "PENDENTE" and str(vencimento) < hoje:
                status_exibir, cor_status = "ATRASADO", "#e74c3c"
            elif status == "PENDENTE":
                status_exibir, cor_status = "PENDENTE", "#f39c12"
            elif status == "PAGO":
                status_exibir = "PAGO" if tipo == "PAGAR" else "RECEBIDO"
                cor_status = "#2ecc71"
            else:
                status_exibir, cor_status = "CANCELADO", "#7f8c8d"

            cor_fundo = "#2b2b2b" if row_idx % 2 == 0 else "transparent"
            row_frame = ctk.CTkFrame(tabela_frame, fg_color=cor_fundo, corner_radius=5)
            row_frame.grid(row=row_idx, column=0, columnspan=len(headers), sticky="ew", pady=2)
            for idx, peso in enumerate(pesos):
                row_frame.grid_columnconfigure(idx, weight=peso, uniform="col_fin")

            ctk.CTkLabel(row_frame, text=descricao, anchor="w", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="ew", padx=10, pady=8)
            ctk.CTkLabel(row_frame, text=categoria).grid(row=0, column=1, sticky="ew", pady=8)
            ctk.CTkLabel(row_frame, text=formatar_moeda_br(valor)).grid(row=0, column=2, sticky="ew", pady=8)
            ctk.CTkLabel(row_frame, text=formatar_data_exibir(vencimento)).grid(row=0, column=3, sticky="ew", pady=8)
            ctk.CTkLabel(row_frame, text=status_exibir, text_color=cor_status, font=("Arial", 12, "bold")).grid(row=0, column=4, sticky="ew", pady=8)

            acoes_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            acoes_frame.grid(row=0, column=5, pady=4, padx=5)

            if status == "PENDENTE":
                texto_baixa = "Pagar" if tipo == "PAGAR" else "Receber"
                btn_baixa = ctk.CTkButton(
                    acoes_frame, text=texto_baixa, width=70, height=26, font=("Arial", 11, "bold"),
                    fg_color="#27ae60", hover_color="#1e8449",
                    command=lambda tid=t_id: self.dar_baixa(tipo, tid)
                )
                btn_baixa.pack(side="left", padx=(0, 5))

                btn_cancelar = ctk.CTkButton(
                    acoes_frame, text="✕", width=30, height=26, font=("Arial", 12, "bold"),
                    fg_color="transparent", border_width=1, border_color="#e74c3c", text_color="#e74c3c",
                    hover_color="#333333",
                    command=lambda tid=t_id: self.cancelar_lancamento(tipo, tid)
                )
                btn_cancelar.pack(side="left")

    def abrir_novo_lancamento(self, tipo):
        from ui.components.modal_titulo_financeiro import ModalTituloFinanceiro
        ModalTituloFinanceiro(master=self.winfo_toplevel(), tipo=tipo, ao_salvar=lambda: self.carregar_titulos(tipo))

    def dar_baixa(self, tipo, id_titulo):
        acao = "pago" if tipo == "PAGAR" else "recebido"
        if not messagebox.askyesno("Confirmar", f"Marcar este título como {acao}?"):
            return

        if marcar_titulo_como_pago(id_titulo, tipo):
            self.carregar_titulos(tipo)
        else:
            messagebox.showerror("Erro", "Não foi possível dar baixa neste título.")

    def cancelar_lancamento(self, tipo, id_titulo):
        if not messagebox.askyesno("Confirmar", "Cancelar este lançamento? Ele deixará de contar nos totais."):
            return

        if cancelar_titulo_financeiro(id_titulo, tipo):
            self.carregar_titulos(tipo)
        else:
            messagebox.showerror("Erro", "Não foi possível cancelar este lançamento.")
