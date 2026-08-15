import customtkinter as ctk
from tkinter import messagebox
from utils.auth import UsuarioSessao, verificar_senha_supervisor


class ModalSangria(ctk.CTkToplevel):
    """
    Modal de Sangria de caixa (atalho F4).
    Retira dinheiro FÍSICO da gaveta e registra a movimentação na tabela
    'movimentacoes_caixa' (tipo='SANGRIA'), vinculada à sessão de caixa atual.

    ⚠️ Regra de Ouro: vendas em Cartão de Crédito/Débito ou PIX não entram no
    saldo disponível aqui — esse dinheiro cai direto na conta da empresa, nunca
    passa pela gaveta. O cálculo do saldo é feito pelo MainPDV/pdv_service
    antes deste modal ser aberto.
    """
    NIVEL_SUPERVISOR = 1

    def __init__(self, master, saldo_disponivel, ao_confirmar):
        super().__init__(master)

        self.saldo_disponivel = float(saldo_disponivel)
        self.ao_confirmar = ao_confirmar  # MainPDV.processar_sangria

        # Trava de segurança: só pede autorização de supervisor se quem está
        # operando a sangria NÃO for, ele mesmo, um supervisor (Nível 1)
        self.exige_autorizacao = UsuarioSessao.nivel != self.NIVEL_SUPERVISOR

        # Configurações da Janela
        self.title("Sangria de Caixa (F4)")
        self.geometry("440x560" if self.exige_autorizacao else "440x420")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")

        self.transient(master)
        self.grab_set()

        self.setup_ui()
        self.configurar_binds()

    def setup_ui(self):
        ctk.CTkLabel(
            self, text="SANGRIA DE CAIXA",
            font=("Arial", 20, "bold"), text_color="#e67e22"
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self, text=f"Disponível na gaveta: R$ {self.saldo_disponivel:.2f}".replace('.', ','),
            font=("Arial", 14, "bold"), text_color="#27ae60"
        ).pack(pady=(0, 15))

        # --- VALOR DA RETIRADA ---
        ctk.CTkLabel(self, text="VALOR DA RETIRADA (R$):", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30)
        self.entry_valor = ctk.CTkEntry(self, height=45, font=("Arial", 18, "bold"), fg_color="#2b2b2b", placeholder_text="0,00")
        self.entry_valor.pack(fill="x", padx=30, pady=(2, 15))
        self.entry_valor.focus()

        # --- MOTIVO / OBSERVAÇÃO ---
        ctk.CTkLabel(self, text="MOTIVO / OBSERVAÇÃO:", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30)
        self.entry_motivo = ctk.CTkEntry(
            self, height=40, font=("Arial", 13), fg_color="#2b2b2b",
            placeholder_text="Ex: Retirada para o cofre central"
        )
        self.entry_motivo.pack(fill="x", padx=30, pady=(2, 15))

        # --- AUTORIZAÇÃO DE SUPERVISOR (SÓ APARECE SE NECESSÁRIO) ---
        if self.exige_autorizacao:
            ctk.CTkLabel(
                self, text="AUTORIZAÇÃO DE SUPERVISOR NECESSÁRIA",
                font=("Arial", 11, "bold"), text_color="#e74c3c"
            ).pack(anchor="w", padx=30, pady=(5, 5))

            self.entry_usuario_super = ctk.CTkEntry(
                self, height=35, font=("Arial", 13), fg_color="#2b2b2b", placeholder_text="Usuário do supervisor"
            )
            self.entry_usuario_super.pack(fill="x", padx=30, pady=(0, 8))

            self.entry_senha_super = ctk.CTkEntry(
                self, height=35, font=("Arial", 13), fg_color="#2b2b2b", placeholder_text="Senha do supervisor", show="*"
            )
            self.entry_senha_super.pack(fill="x", padx=30, pady=(0, 5))

        # --- BOTÃO CONFIRMAR ---
        self.btn_confirmar = ctk.CTkButton(
            self, text="CONFIRMAR SANGRIA (Enter)",
            command=self.validar_e_confirmar,
            fg_color="#e67e22", hover_color="#d35400",
            height=45, font=("Arial", 14, "bold")
        )
        self.btn_confirmar.pack(fill="x", padx=30, pady=(15, 20), side="bottom")

    def configurar_binds(self):
        self.bind("<Return>", lambda e: self.validar_e_confirmar())
        self.bind("<Escape>", lambda e: self.destroy())

    def validar_e_confirmar(self):
        valor_texto = self.entry_valor.get().strip().replace(',', '.')
        motivo = self.entry_motivo.get().strip()

        if not valor_texto:
            messagebox.showwarning("Atenção", "Informe o valor da retirada.")
            return

        try:
            valor = float(valor_texto)
        except ValueError:
            messagebox.showwarning("Atenção", "Valor inválido.")
            return

        if valor <= 0:
            messagebox.showwarning("Atenção", "O valor da retirada deve ser maior que zero.")
            return

        # --- VALIDAÇÃO DE SALDO DISPONÍVEL ---
        if valor > self.saldo_disponivel:
            messagebox.showerror(
                "Saldo Insuficiente",
                f"A gaveta possui apenas R$ {self.saldo_disponivel:.2f}".replace('.', ',') +
                " disponível.\nNão é possível retirar um valor maior que o saldo em caixa."
            )
            return

        if not motivo:
            messagebox.showwarning("Atenção", "Informe o motivo/observação da retirada.")
            return

        # --- TRAVA DE SEGURANÇA: autorização de supervisor (Nível 1) ---
        if self.exige_autorizacao:
            usuario_super = self.entry_usuario_super.get().strip()
            senha_super = self.entry_senha_super.get()

            if not usuario_super or not senha_super:
                messagebox.showwarning("Atenção", "Informe o usuário e a senha do supervisor.")
                return

            if not verificar_senha_supervisor(usuario_super, senha_super):
                messagebox.showerror(
                    "Não Autorizado",
                    "Usuário/senha inválidos, ou o usuário informado não é um supervisor (Nível 1)."
                )
                return

        self.ao_confirmar(valor, motivo)
        self.destroy()
