import customtkinter as ctk
from tkinter import messagebox


class ModalClienteCPF(ctk.CTkToplevel):
    """
    Modal de identificação do cliente na venda atual (atalho F3).
    O CPF informado fica apenas em memória, na instância do MainPDV
    (self.cpf_cliente) — não é gravado no Supabase neste momento. Ele será
    usado futuramente na emissão/impressão da notinha ao finalizar a venda.
    """
    def __init__(self, master, cpf_atual, ao_salvar):
        super().__init__(master)

        self.ao_salvar = ao_salvar  # MainPDV.definir_cpf_cliente

        # Configurações da Janela
        self.title("Identificar Cliente (F3)")
        self.geometry("420x280")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")

        self.transient(master)
        self.grab_set()

        self.setup_ui()
        self.configurar_binds()

        # Se a venda atual já tem um CPF vinculado, pré-carrega o campo para edição
        if cpf_atual:
            self.entry_cpf.insert(0, cpf_atual)

    def setup_ui(self):
        ctk.CTkLabel(
            self, text="IDENTIFICAR CLIENTE",
            font=("Arial", 20, "bold"), text_color="#3498db"
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            self, text="CPF vinculado a esta venda (usado na nota ao finalizar)",
            font=("Arial", 11), text_color="gray"
        ).pack(pady=(0, 20))

        self.entry_cpf = ctk.CTkEntry(
            self,
            placeholder_text="000.000.000-00",
            height=50,
            font=("Arial", 20),
            fg_color="#2b2b2b",
            justify="center"
        )
        self.entry_cpf.pack(padx=40, fill="x")
        self.entry_cpf.focus()

        self.btn_salvar = ctk.CTkButton(
            self, text="SALVAR (Enter)",
            command=self.salvar_cpf,
            fg_color="#27ae60", hover_color="#219150",
            height=45, font=("Arial", 14, "bold")
        )
        self.btn_salvar.pack(padx=40, pady=(25, 10), fill="x")

        self.btn_remover = ctk.CTkButton(
            self, text="Venda sem CPF (remover)",
            command=self.remover_cpf,
            fg_color="transparent", border_width=1, border_color="#e74c3c",
            hover_color="#333333", text_color="#e74c3c",
            height=32, font=("Arial", 11)
        )
        self.btn_remover.pack(padx=40, pady=(0, 10), fill="x")

    def configurar_binds(self):
        self.entry_cpf.bind("<KeyRelease>", self.aplicar_mascara_cpf)
        self.entry_cpf.bind("<Return>", lambda e: self.salvar_cpf())
        self.bind("<Escape>", lambda e: self.destroy())

    def aplicar_mascara_cpf(self, event=None):
        """Formata o CPF em tempo real no padrão 000.000.000-00 enquanto o operador digita."""
        apenas_numeros = "".join(filter(str.isdigit, self.entry_cpf.get()))[:11]

        cpf_formatado = apenas_numeros
        if len(apenas_numeros) > 9:
            cpf_formatado = f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"
        elif len(apenas_numeros) > 6:
            cpf_formatado = f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:]}"
        elif len(apenas_numeros) > 3:
            cpf_formatado = f"{apenas_numeros[:3]}.{apenas_numeros[3:]}"

        self.entry_cpf.delete(0, 'end')
        self.entry_cpf.insert(0, cpf_formatado)

    def validar_cpf(self, cpf_numeros):
        """Valida os dígitos verificadores do CPF (algoritmo padrão da Receita Federal)."""
        if len(cpf_numeros) != 11 or len(set(cpf_numeros)) == 1:
            return False

        soma = sum(int(cpf_numeros[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10
        if digito1 != int(cpf_numeros[9]):
            return False

        soma = sum(int(cpf_numeros[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        if digito2 != int(cpf_numeros[10]):
            return False

        return True

    def salvar_cpf(self):
        cpf_formatado = self.entry_cpf.get().strip()
        apenas_numeros = "".join(filter(str.isdigit, cpf_formatado))

        if not apenas_numeros:
            messagebox.showwarning("Atenção", "Digite um CPF ou use 'Venda sem CPF'.")
            return

        if len(apenas_numeros) != 11:
            messagebox.showwarning("Atenção", "O CPF deve conter 11 dígitos.")
            return

        if not self.validar_cpf(apenas_numeros):
            # Não bloqueia o operador de caixa por um dígito verificador incorreto,
            # apenas confirma se ele realmente quer prosseguir mesmo assim
            if not messagebox.askyesno(
                "CPF Inválido",
                "Os dígitos verificadores desse CPF não conferem.\nDeseja salvar mesmo assim?"
            ):
                return

        self.ao_salvar(cpf_formatado)
        self.destroy()

    def remover_cpf(self):
        """Desvincula qualquer CPF já associado à venda atual."""
        self.ao_salvar(None)
        self.destroy()
