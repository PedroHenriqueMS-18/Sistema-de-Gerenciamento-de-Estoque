import customtkinter as ctk
from tkinter import messagebox

class ModalAbertura(ctk.CTkToplevel):
    def __init__(self, master, ao_confirmar):
        super().__init__(master)
        
        self.ao_confirmar = ao_confirmar # Função que vai destravar o PDV
        
        self.title("Abertura de Caixa - Estimaí")
        self.geometry("400x350")
        self.resizable(False, False)
        
        # Faz o modal ficar na frente e impede cliques no PDV atrás
        self.transient(master)
        self.grab_set()
        
        self.setup_ui()

    def setup_ui(self):
        # Título
        ctk.CTkLabel(self, text="ABERTURA DE CAIXA", font=("Arial", 20, "bold")).pack(pady=(30, 10))
        ctk.CTkLabel(self, text="Informe o valor de suprimento (troco inicial):", font=("Arial", 12), text_color="gray").pack(pady=(0, 20))

        # Campo de Valor
        self.entry_valor = ctk.CTkEntry(self, width=250, height=45, placeholder_text="R$ 0,00", font=("Arial", 18), justify="center")
        self.entry_valor.pack(pady=10)
        self.entry_valor.focus_set()

        # Bind do Enter para confirmar rápido
        self.entry_valor.bind("<Return>", lambda e: self.confirmar())

        # Botão Confirmar
        self.btn_confirmar = ctk.CTkButton(
            self, text="CONFIRMAR ABERTURA", 
            fg_color="#27ae60", hover_color="#219150",
            font=("Arial", 14, "bold"),
            height=45, width=250,
            command=self.confirmar
        )
        self.btn_confirmar.pack(pady=30)

    def confirmar(self):
        valor_str = self.entry_valor.get().replace(',', '.')
        try:
            valor_float = float(valor_str) if valor_str else 0.0
            
            # 1. Aqui chamaremos a função para salvar no banco (depois)
            # 2. Chama o callback para destravar o PDV
            self.ao_confirmar(valor_float)
            self.destroy()
        except ValueError:
            messagebox.showwarning("Erro", "Por favor, insira um valor numérico válido!")