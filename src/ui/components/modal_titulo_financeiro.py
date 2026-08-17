import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from utils.financeiro_service import criar_titulo_financeiro
from utils.fornec_service import buscar_fornecedores_db


class ModalTituloFinanceiro(ctk.CTkToplevel):
    """
    Modal de lançamento de um novo título financeiro — Conta a Pagar ou a Receber
    (definido por 'tipo', vindo da aba em que o usuário clicou em '+ Novo Lançamento'
    na tela de Financeiro). Módulo restrito a supervisores (Nível 1), acessado pela
    MainWindow — totalmente fora do fluxo do PDV.
    """
    CATEGORIAS_PAGAR = ["Fornecedor", "Aluguel", "Salário", "Água/Luz/Internet", "Imposto", "Manutenção", "Outros"]
    CATEGORIAS_RECEBER = ["Cliente", "Cartão (Repasse)", "Aluguel Recebido", "Empréstimo", "Outros"]

    def __init__(self, master, tipo, ao_salvar):
        super().__init__(master)

        self.tipo = tipo  # 'PAGAR' ou 'RECEBER'
        self.ao_salvar = ao_salvar

        titulo_janela = "Nova Conta a Pagar" if tipo == "PAGAR" else "Nova Conta a Receber"
        self.title(titulo_janela)
        self.geometry("460x640")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")

        self.transient(master)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        cor_destaque = "#e74c3c" if self.tipo == "PAGAR" else "#27ae60"
        texto_titulo = "NOVA CONTA A PAGAR" if self.tipo == "PAGAR" else "NOVA CONTA A RECEBER"

        ctk.CTkLabel(self, text=texto_titulo, font=("Arial", 20, "bold"), text_color=cor_destaque).pack(pady=(20, 15))

        # --- DESCRIÇÃO ---
        ctk.CTkLabel(self, text="DESCRIÇÃO:", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30)
        self.entry_descricao = ctk.CTkEntry(
            self, height=40, font=("Arial", 13), fg_color="#2b2b2b",
            placeholder_text="Ex: Aluguel do galpão - Agosto"
        )
        self.entry_descricao.pack(fill="x", padx=30, pady=(2, 12))
        self.entry_descricao.focus()

        # --- CATEGORIA ---
        ctk.CTkLabel(self, text="CATEGORIA:", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30)
        categorias = self.CATEGORIAS_PAGAR if self.tipo == "PAGAR" else self.CATEGORIAS_RECEBER
        self.categoria_var = ctk.StringVar(value=categorias[0])
        self.menu_categoria = ctk.CTkOptionMenu(self, values=categorias, variable=self.categoria_var, height=40)
        self.menu_categoria.pack(fill="x", padx=30, pady=(2, 12))

        # --- VALOR E VENCIMENTO (lado a lado) ---
        linha_frame = ctk.CTkFrame(self, fg_color="transparent")
        linha_frame.pack(fill="x", padx=30, pady=(0, 12))

        col_valor = ctk.CTkFrame(linha_frame, fg_color="transparent")
        col_valor.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(col_valor, text="VALOR (R$):", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w")
        self.entry_valor = ctk.CTkEntry(col_valor, height=40, font=("Arial", 14, "bold"), fg_color="#2b2b2b", placeholder_text="0,00")
        self.entry_valor.pack(fill="x", pady=(2, 0))

        col_venc = ctk.CTkFrame(linha_frame, fg_color="transparent")
        col_venc.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(col_venc, text="VENCIMENTO:", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w")
        self.entry_vencimento = ctk.CTkEntry(col_venc, height=40, font=("Arial", 14), fg_color="#2b2b2b", placeholder_text="dd/mm/aaaa")
        self.entry_vencimento.pack(fill="x", pady=(2, 0))

        # --- FORNECEDOR (OPCIONAL, SÓ EM CONTAS A PAGAR) ---
        self.fornecedor_var = None
        self.mapa_fornecedores = {}
        if self.tipo == "PAGAR":
            ctk.CTkLabel(self, text="FORNECEDOR (opcional):", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30)

            self.mapa_fornecedores = {"Nenhum": None}
            for fornecedor in buscar_fornecedores_db():  # só ativos, por padrão
                f_id, f_nome = fornecedor[0], fornecedor[1]
                self.mapa_fornecedores[f_nome] = f_id

            self.fornecedor_var = ctk.StringVar(value="Nenhum")
            self.menu_fornecedor = ctk.CTkOptionMenu(
                self, values=list(self.mapa_fornecedores.keys()), variable=self.fornecedor_var, height=40
            )
            self.menu_fornecedor.pack(fill="x", padx=30, pady=(2, 12))

        # --- OBSERVAÇÃO ---
        ctk.CTkLabel(self, text="OBSERVAÇÃO (opcional):", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30)
        self.entry_observacao = ctk.CTkEntry(self, height=40, font=("Arial", 13), fg_color="#2b2b2b")
        self.entry_observacao.pack(fill="x", padx=30, pady=(2, 20))

        self.btn_salvar = ctk.CTkButton(
            self, text="SALVAR LANÇAMENTO",
            command=self.salvar,
            fg_color=cor_destaque, hover_color=("#c0392b" if self.tipo == "PAGAR" else "#1e8449"),
            height=45, font=("Arial", 14, "bold")
        )
        self.btn_salvar.pack(fill="x", padx=30, pady=(0, 20), side="bottom")

        self.bind("<Return>", lambda e: self.salvar())
        self.bind("<Escape>", lambda e: self.destroy())

    def salvar(self):
        descricao = self.entry_descricao.get().strip()
        categoria = self.categoria_var.get()
        valor_texto = self.entry_valor.get().strip().replace(',', '.')
        vencimento_texto = self.entry_vencimento.get().strip()
        observacao = self.entry_observacao.get().strip()

        if not descricao:
            messagebox.showwarning("Atenção", "Informe a descrição do lançamento.")
            return

        try:
            valor = float(valor_texto)
            if valor <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um valor válido (maior que zero).")
            return

        try:
            vencimento_iso = datetime.strptime(vencimento_texto, "%d/%m/%Y").date().isoformat()
        except ValueError:
            messagebox.showwarning("Atenção", "Informe a data de vencimento no formato dd/mm/aaaa.")
            return

        id_fornecedor = self.mapa_fornecedores.get(self.fornecedor_var.get()) if self.fornecedor_var else None

        dados = {
            "tipo": self.tipo,
            "descricao": descricao,
            "categoria": categoria,
            "valor": valor,
            "vencimento": vencimento_iso,
            "id_fornecedor": id_fornecedor,
            "observacao": observacao
        }

        sucesso, resultado = criar_titulo_financeiro(dados)

        if sucesso:
            messagebox.showinfo("Sucesso", "Lançamento registrado com sucesso!")
            if self.ao_salvar:
                self.ao_salvar()
            self.destroy()
        else:
            messagebox.showerror("Erro", f"Não foi possível salvar: {resultado}")
