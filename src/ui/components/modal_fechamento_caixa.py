import customtkinter as ctk
from tkinter import messagebox


class ModalFechamentoCaixa(ctk.CTkToplevel):
    """
    Modal de Fechamento de Caixa (atalho F12).
    Conferência CEGA: o operador informa o dinheiro físico contado na gaveta sem
    que a tela revele o saldo esperado — a conciliação completa (com a diferença
    de quebra/sobra) só acontece depois, no espelho gerado pelo MainPDV/pdv_service.
    """
    def __init__(self, master, ao_confirmar):
        super().__init__(master)

        self.ao_confirmar = ao_confirmar  # MainPDV.processar_fechamento_caixa

        # Configurações da Janela
        self.title("Fechamento de Caixa (F12)")
        self.geometry("440x430")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")

        self.transient(master)
        self.grab_set()

        self.setup_ui()
        self.configurar_binds()

    def setup_ui(self):
        ctk.CTkLabel(
            self, text="FECHAMENTO DE CAIXA",
            font=("Arial", 20, "bold"), text_color="#e74c3c"
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self, text="Conte o dinheiro físico da gaveta antes de continuar",
            font=("Arial", 11), text_color="gray"
        ).pack(pady=(0, 20))

        # --- VALOR CONTADO NA GAVETA ---
        ctk.CTkLabel(self, text="VALOR CONTADO NA GAVETA (R$):", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30)
        self.entry_valor = ctk.CTkEntry(self, height=45, font=("Arial", 18, "bold"), fg_color="#2b2b2b", placeholder_text="0,00")
        self.entry_valor.pack(fill="x", padx=30, pady=(2, 15))
        self.entry_valor.focus()

        # --- OBSERVAÇÃO / JUSTIFICATIVA ---
        ctk.CTkLabel(self, text="OBSERVAÇÃO / JUSTIFICATIVA (opcional):", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30)
        self.entry_observacao = ctk.CTkEntry(
            self, height=40, font=("Arial", 13), fg_color="#2b2b2b",
            placeholder_text="Ex: Notas rasgadas separadas para troca no banco"
        )
        self.entry_observacao.pack(fill="x", padx=30, pady=(2, 15))

        ctk.CTkLabel(
            self,
            text="Ao confirmar, o turno é encerrado e o caixa fica bloqueado\npara novas vendas até a próxima abertura.",
            font=("Arial", 10), text_color="gray", justify="center"
        ).pack(pady=(0, 5))

        # --- BOTÃO CONFIRMAR ---
        self.btn_confirmar = ctk.CTkButton(
            self, text="ENCERRAR TURNO (Enter)",
            command=self.validar_e_confirmar,
            fg_color="#e74c3c", hover_color="#c0392b",
            height=45, font=("Arial", 14, "bold")
        )
        self.btn_confirmar.pack(fill="x", padx=30, pady=(10, 20), side="bottom")

    def configurar_binds(self):
        self.bind("<Return>", lambda e: self.validar_e_confirmar())
        self.bind("<Escape>", lambda e: self.destroy())

    def validar_e_confirmar(self):
        valor_texto = self.entry_valor.get().strip().replace(',', '.')

        if not valor_texto:
            messagebox.showwarning("Atenção", "Informe o valor contado na gaveta.")
            return

        try:
            valor = float(valor_texto)
        except ValueError:
            messagebox.showwarning("Atenção", "Valor inválido.")
            return

        if valor < 0:
            messagebox.showwarning("Atenção", "O valor contado não pode ser negativo.")
            return

        observacao = self.entry_observacao.get().strip()

        # --- AVISO ANTES DE ENCERRAR O TURNO ---
        if not messagebox.askyesno(
            "Confirmar Fechamento",
            "Tem certeza que deseja encerrar o turno?\nEssa ação não pode ser desfeita."
        ):
            return

        self.ao_confirmar(valor, observacao)
        self.destroy()
