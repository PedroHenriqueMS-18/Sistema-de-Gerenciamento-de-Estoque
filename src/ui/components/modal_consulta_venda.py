import customtkinter as ctk
from tkinter import messagebox
from utils.auth import UsuarioSessao, verificar_senha_supervisor
from utils.pdv_service import buscar_vendas, estornar_venda


class ModalConsultaVenda(ctk.CTkToplevel):
    """
    Modal de Consulta de Venda (PDV, atalho F7). Lista o histórico de vendas
    (concluídas e já devolvidas) — sem filtro de data por padrão, traz tudo — com
    busca por número da venda ou nome do operador. Duplo clique numa venda
    CONCLUÍDA abre a confirmação de estorno: devolve os itens ao estoque e marca
    a venda como DEVOLVIDA, o que já a remove automaticamente de todos os cálculos
    de faturamento/caixa (que só contam status='CONCLUIDA').

    Trava de segurança: se quem está operando não for supervisor (Nível 1), o
    estorno exige usuário/senha de um supervisor — mesmo mecanismo já usado na
    Sangria de caixa.
    """
    NIVEL_SUPERVISOR = 1

    def __init__(self, master):
        super().__init__(master)

        self.resultados_atuais = []

        self.title("Consultar Venda (F7)")
        self.geometry("820x600")
        self.configure(fg_color="#1a1a1a")

        self.transient(master)
        self.grab_set()

        self.setup_ui()
        self.configurar_binds()
        self.executar_busca()

    def setup_ui(self):
        ctk.CTkLabel(self, text="CONSULTAR VENDA", font=("Arial", 20, "bold"), text_color="#3498db").pack(pady=(15, 10))

        # --- BUSCA E FILTRO ---
        busca_frame = ctk.CTkFrame(self, fg_color="transparent")
        busca_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.entry_termo = ctk.CTkEntry(
            busca_frame, placeholder_text="Buscar por nº da venda ou nome do operador...",
            height=42, font=("Arial", 14), fg_color="#2b2b2b"
        )
        self.entry_termo.pack(side="left", fill="x", expand=True)
        self.entry_termo.focus()

        self.status_var = ctk.StringVar(value="TODAS")
        self.menu_status = ctk.CTkOptionMenu(
            busca_frame, values=["TODAS", "CONCLUIDA", "DEVOLVIDA"], variable=self.status_var,
            width=140, command=lambda e: self.executar_busca()
        )
        self.menu_status.pack(side="left", padx=(10, 0))

        self.btn_buscar = ctk.CTkButton(busca_frame, text="BUSCAR", command=self.executar_busca, height=42, width=100)
        self.btn_buscar.pack(side="left", padx=(10, 0))

        # --- TABELA ---
        self.table_weights = [1, 2, 1, 1, 1, 1]

        self.tabela_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.tabela_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.render_cabecalho()

        ctk.CTkLabel(
            self,
            text="Dê um duplo clique numa venda concluída para estorná-la (devolve o estoque e remove do faturamento).",
            font=("Arial", 11), text_color="gray"
        ).pack(pady=(0, 15))

    def render_cabecalho(self):
        headers = ["Nº VENDA", "OPERADOR", "VALOR", "DATA", "HORA", "STATUS"]

        header_row = ctk.CTkFrame(self.tabela_frame, fg_color="#3d3d3d")
        header_row.pack(fill="x", pady=(0, 5))

        for i, texto in enumerate(headers):
            lbl = ctk.CTkLabel(header_row, text=texto, font=("Arial", 12, "bold"), text_color="gray", anchor="center")
            lbl.grid(row=0, column=i, sticky="nsew", pady=8)
            header_row.grid_columnconfigure(i, weight=self.table_weights[i], uniform="col_venda")

    def configurar_binds(self):
        self.entry_termo.bind("<Return>", lambda e: self.executar_busca())
        self.bind("<Escape>", lambda e: self.destroy())

    def executar_busca(self):
        termo = self.entry_termo.get().strip()
        status_filtro = self.status_var.get()
        self.resultados_atuais = buscar_vendas(termo, status_filtro)
        self.renderizar_resultados()

    def renderizar_resultados(self):
        for widget in self.tabela_frame.winfo_children()[1:]:
            widget.destroy()

        if not self.resultados_atuais:
            ctk.CTkLabel(self.tabela_frame, text="Nenhuma venda encontrada.", text_color="gray").pack(pady=20)
            return

        for i, venda in enumerate(self.resultados_atuais):
            id_venda, nome_operador, valor_total, data_venda, hora_venda, status, id_forma = venda
            cor_linha = "#333333" if i % 2 == 0 else "transparent"
            cor_status = "#2ecc71" if status == "CONCLUIDA" else "#e74c3c"

            row_frame = ctk.CTkFrame(self.tabela_frame, fg_color=cor_linha, cursor=("hand2" if status == "CONCLUIDA" else "arrow"))
            row_frame.pack(fill="x", pady=0)

            dados_linha = [
                f"#{id_venda}",
                str(nome_operador),
                f"R$ {valor_total:.2f}".replace('.', ','),
                str(data_venda),
                str(hora_venda)[:8],
            ]

            widgets_linha = [row_frame]
            for col, texto in enumerate(dados_linha):
                lbl = ctk.CTkLabel(row_frame, text=texto, font=("Arial", 13), text_color="white", anchor="center")
                lbl.grid(row=0, column=col, sticky="nsew", pady=8)
                row_frame.grid_columnconfigure(col, weight=self.table_weights[col], uniform="col_venda")
                widgets_linha.append(lbl)

            lbl_status = ctk.CTkLabel(row_frame, text=status, font=("Arial", 12, "bold"), text_color=cor_status, anchor="center")
            lbl_status.grid(row=0, column=5, sticky="nsew", pady=8)
            row_frame.grid_columnconfigure(5, weight=self.table_weights[5], uniform="col_venda")
            widgets_linha.append(lbl_status)

            # Só vendas CONCLUIDA podem ser estornadas via duplo clique
            if status == "CONCLUIDA":
                for widget in widgets_linha:
                    widget.bind("<Double-Button-1>", lambda e, vid=id_venda, val=valor_total: self.confirmar_estorno(vid, val))

    def confirmar_estorno(self, id_venda, valor_total):
        valor_exibir = f"R$ {valor_total:.2f}".replace('.', ',')

        if not messagebox.askyesno(
            "Cancelar Venda",
            f"Deseja realmente cancelar (estornar) a venda #{id_venda}, no valor de {valor_exibir}?\n\n"
            "Os produtos voltam ao estoque e o valor sai do faturamento."
        ):
            return

        # --- TRAVA DE SEGURANÇA: exige supervisor se quem confirma não for Nível 1 ---
        if UsuarioSessao.nivel != self.NIVEL_SUPERVISOR:
            usuario_super, senha_super = self.pedir_autorizacao_supervisor()

            if usuario_super is None:
                return  # autorização cancelada pelo usuário

            if not usuario_super or not senha_super or not verificar_senha_supervisor(usuario_super, senha_super):
                messagebox.showerror("Não Autorizado", "Usuário/senha inválidos, ou o usuário informado não é supervisor (Nível 1).")
                return

        sucesso, resultado = estornar_venda(id_venda)

        if sucesso:
            messagebox.showinfo("Venda Estornada", f"Venda #{id_venda} estornada com sucesso!\nEstoque devolvido.")
            self.executar_busca()
        else:
            messagebox.showerror("Erro", f"Não foi possível estornar a venda: {resultado}")

    def pedir_autorizacao_supervisor(self):
        """Abre uma janela pedindo usuário/senha de supervisor. Retorna (usuario, senha), ou (None, None) se cancelado."""
        resultado = {"usuario": None, "senha": None}

        janela = ctk.CTkToplevel(self)
        janela.title("Autorização de Supervisor")
        janela.geometry("360x260")
        janela.resizable(False, False)
        janela.configure(fg_color="#1a1a1a")
        janela.transient(self)
        janela.grab_set()

        ctk.CTkLabel(janela, text="AUTORIZAÇÃO NECESSÁRIA", font=("Arial", 15, "bold"), text_color="#e74c3c").pack(pady=(20, 10))
        ctk.CTkLabel(janela, text="Só um supervisor (Nível 1) pode\nautorizar este estorno.", font=("Arial", 11), text_color="gray").pack(pady=(0, 10))

        entry_usuario = ctk.CTkEntry(janela, placeholder_text="Usuário do supervisor", height=38, fg_color="#2b2b2b")
        entry_usuario.pack(fill="x", padx=25, pady=(0, 8))
        entry_usuario.focus()

        entry_senha = ctk.CTkEntry(janela, placeholder_text="Senha do supervisor", height=38, fg_color="#2b2b2b", show="*")
        entry_senha.pack(fill="x", padx=25, pady=(0, 15))

        def confirmar():
            resultado["usuario"] = entry_usuario.get().strip()
            resultado["senha"] = entry_senha.get()
            janela.destroy()

        entry_senha.bind("<Return>", lambda e: confirmar())
        janela.bind("<Escape>", lambda e: janela.destroy())

        ctk.CTkButton(
            janela, text="Autorizar", command=confirmar,
            fg_color="#e74c3c", hover_color="#c0392b", height=40
        ).pack(fill="x", padx=25)

        self.wait_window(janela)  # bloqueia até a mini-janela fechar
        return resultado["usuario"], resultado["senha"]
