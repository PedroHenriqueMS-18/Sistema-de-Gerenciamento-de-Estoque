import customtkinter as ctk
from tkinter import messagebox
from utils.compras_service import buscar_itens_pedido, confirmar_recebimento_pedido
from utils.financeiro_service import formatar_moeda_br


class ModalConfirmarRecebimento(ctk.CTkToplevel):
    """
    Modal de conferência de recebimento de um Pedido de Compra PENDENTE. Lista os
    itens com a quantidade pedida (fixa) ao lado de um campo editável de quantidade
    recebida (pré-preenchido igual à pedida — o operador só mexe se veio diferente).
    Ao confirmar, dá entrada no estoque com a quantidade real e mostra o resumo de
    divergências (o que faltou), item por item.
    """
    def __init__(self, master, id_pedido, nome_fornecedor, ao_confirmar):
        super().__init__(master)

        self.id_pedido = id_pedido
        self.ao_confirmar = ao_confirmar
        self.entradas_qtd = {}  # id_item -> CTkEntry

        self.title(f"Confirmar Recebimento - Pedido #{id_pedido}")
        self.geometry("640x560")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")

        self.transient(master)
        self.grab_set()

        self.itens = buscar_itens_pedido(id_pedido)
        self.setup_ui(nome_fornecedor)

    def setup_ui(self, nome_fornecedor):
        ctk.CTkLabel(self, text="CONFIRMAR RECEBIMENTO", font=("Arial", 20, "bold"), text_color="#27ae60").pack(pady=(20, 5))
        ctk.CTkLabel(self, text=f"Pedido #{self.id_pedido} — {nome_fornecedor}", font=("Arial", 12), text_color="gray").pack(pady=(0, 15))

        # --- CABEÇALHO DA LISTA ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30)
        for texto, peso in [("Produto", 3), ("Pedido", 1), ("Recebido", 1)]:
            ctk.CTkLabel(header, text=texto, font=("Arial", 12, "bold"), text_color="gray").pack(
                side="left", fill="x", expand=(peso == 3), padx=5
            )

        # --- LISTA DE ITENS ---
        self.lista_frame = ctk.CTkScrollableFrame(self, fg_color="#242424", corner_radius=10)
        self.lista_frame.pack(fill="both", expand=True, padx=30, pady=(5, 15))

        if not self.itens:
            ctk.CTkLabel(self.lista_frame, text="Este pedido não tem itens.", text_color="gray").pack(pady=20)

        for id_item, id_produto, nome_produto, qtd_pedida, qtd_recebida, custo_unitario in self.itens:
            linha = ctk.CTkFrame(self.lista_frame, fg_color="transparent")
            linha.pack(fill="x", pady=4)

            ctk.CTkLabel(linha, text=nome_produto, anchor="w").pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(linha, text=str(qtd_pedida), width=50).pack(side="left", padx=5)

            entry_recebido = ctk.CTkEntry(linha, width=60, fg_color="#2b2b2b", justify="center")
            entry_recebido.insert(0, str(qtd_pedida))  # já vem pré-preenchido igual ao pedido
            entry_recebido.pack(side="left", padx=5)

            self.entradas_qtd[id_item] = {
                "entry": entry_recebido,
                "id_produto": id_produto,
                "nome_produto": nome_produto,
                "quantidade_pedida": qtd_pedida,
                "custo_unitario": custo_unitario
            }

        self.btn_confirmar = ctk.CTkButton(
            self, text="CONFIRMAR RECEBIMENTO",
            command=self.confirmar,
            fg_color="#27ae60", hover_color="#1e8449",
            height=45, font=("Arial", 14, "bold")
        )
        self.btn_confirmar.pack(fill="x", padx=30, pady=(0, 20))

        self.bind("<Escape>", lambda e: self.destroy())

    def confirmar(self):
        itens_recebidos = []

        for id_item, dados in self.entradas_qtd.items():
            texto_qtd = dados["entry"].get().strip()
            try:
                qtd_recebida = int(texto_qtd)
                if qtd_recebida < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Atenção", f"Quantidade recebida inválida para '{dados['nome_produto']}'.")
                return

            itens_recebidos.append({
                "id_item": id_item,
                "id_produto": dados["id_produto"],
                "nome_produto": dados["nome_produto"],
                "quantidade_pedida": dados["quantidade_pedida"],
                "quantidade_recebida": qtd_recebida,
                "custo_unitario": dados["custo_unitario"]
            })

        if not messagebox.askyesno(
            "Confirmar Recebimento",
            "Confirmar o recebimento deste pedido?\nO estoque será atualizado com as quantidades informadas."
        ):
            return

        sucesso, resultado = confirmar_recebimento_pedido(self.id_pedido, itens_recebidos)

        if not sucesso:
            messagebox.showerror("Erro", f"Não foi possível confirmar o recebimento: {resultado}")
            return

        divergencias = resultado["divergencias"]
        valor_pedido = resultado["valor_pedido"]
        valor_recebido = resultado["valor_recebido"]
        ajuste_titulo = resultado["ajuste_titulo"]

        partes_mensagem = []

        if divergencias:
            linhas = [
                f"• {d['nome_produto']}: pedido {d['quantidade_pedida']}, recebido {d['quantidade_recebida']} "
                f"({'faltou ' + str(d['diferenca']) if d['diferenca'] > 0 else 'excedente de ' + str(abs(d['diferenca']))})"
                for d in divergencias
            ]
            partes_mensagem.append("Diferença de quantidade:\n" + "\n".join(linhas))

        if abs(valor_recebido - valor_pedido) > 0.004:
            partes_mensagem.append(
                f"Valor do pedido: {formatar_moeda_br(valor_pedido)}\n"
                f"Valor realmente recebido: {formatar_moeda_br(valor_recebido)}"
            )
            if ajuste_titulo is None:
                partes_mensagem.append("A conta a pagar no Financeiro foi ajustada automaticamente para esse valor.")
            else:
                partes_mensagem.append(f"⚠️ A conta a pagar NÃO foi ajustada: {ajuste_titulo}")

        if partes_mensagem:
            messagebox.showwarning("Recebimento Confirmado (com divergência)", "\n\n".join(partes_mensagem))
        else:
            messagebox.showinfo("Recebimento Confirmado", "Pedido recebido integralmente, sem divergências!")

        if self.ao_confirmar:
            self.ao_confirmar()
        self.destroy()
