import customtkinter as ctk

class ModalPagamento(ctk.CTkToplevel):
    def __init__(self, master, total_venda, ao_confirmar):
        super().__init__(master)
        
        self.total_venda = float(total_venda)
        self.ao_confirmar = ao_confirmar # Função que vai salvar no banco
        
        # Configurações da Janela
        self.title("Fechamento de Venda")
        self.geometry("450x400")
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")
        
        # Garante que o usuário interaja apenas com essa janela (Modal)
        self.transient(master)
        self.grab_set()

        # Dicionário de Regras de Negócio
        self.REGRAS_PAGAMENTO = {
            "1": {"nome": "DINHEIRO", "pede_valor": True},
            "2": {"nome": "CARTÃO CRÉDITO", "pede_valor": False},
            "3": {"nome": "CARTÃO DÉBITO", "pede_valor": False},
            "4": {"nome": "PIX", "pede_valor": False},
            "5": {"nome": "CHEQUE", "pede_valor": True}
        }

        self.setup_ui()
        self.configurar_binds()

    def setup_ui(self):
        # Título Principal
        ctk.CTkLabel(self, text="FINALIZAR VENDA", font=("Arial", 20, "bold"), text_color="#3498db").pack(pady=15)

        # Exibição do Total do Caixa
        self.lbl_total_venda = ctk.CTkLabel(
            self, 
            text=f"TOTAL: R$ {self.total_venda:.2f}".replace('.', ','), 
            font=("Arial", 28, "bold"), 
            text_color="#27ae60"
        )
        self.lbl_total_venda.pack(pady=10)

        # --- FRAME DA FORMA DE PAGAMENTO (CÓDIGO + TEXTO) ---
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=10)

        # Campo Código (Quadrado pequeno)
        self.entry_codigo = ctk.CTkEntry(form_frame, width=45, height=35, font=("Arial", 16, "bold"), justify="center")
        self.entry_codigo.pack(side="left", padx=(0, 10))
        self.entry_codigo.focus() # Foco começa aqui

        # Campo Descrição da Forma (Maior e Desabilitado)
        self.entry_descricao = ctk.CTkEntry(form_frame, height=35, font=("Arial", 14, "bold"), fg_color="#2b2b2b", text_color="#aaaaaa")
        self.entry_descricao.insert(0, "DIGITE O CÓDIGO...")
        self.entry_descricao.configure(state="disabled")
        self.entry_descricao.pack(side="left", fill="x", expand=True)

        # --- CAMPO VALOR RECEBIDO ---
        ctk.CTkLabel(self, text="VALOR RECEBIDO:", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", padx=30)
        self.entry_recebido = ctk.CTkEntry(self, height=40, font=("Arial", 18, "bold"), justify="right")
        self.entry_recebido.pack(fill="x", padx=30, pady=(2, 10))
        self.entry_recebido.configure(state="disabled") # Começa travado

        # --- DISPLAY DE TROCO DESTACO ---
        self.lbl_troco = ctk.CTkLabel(self, text="TROCO: R$ 0,00", font=("Arial", 24, "bold"), text_color="#e67e22")
        self.lbl_troco.pack(pady=15)

        # Botão Finalizar
        self.btn_confirmar = ctk.CTkButton(
            self, 
            text="CONFIRMAR (Enter)", 
            fg_color="#27ae60", 
            hover_color="#218c53", 
            height=45, 
            font=("Arial", 14, "bold"),
            command=self.validar_e_concluir
        )
        self.btn_confirmar.pack(fill="x", padx=30, side="bottom", pady=20)

    def configurar_binds(self):
        # Quando soltar a tecla no campo código, processa qual é a forma de pagamento
        self.entry_codigo.bind("<KeyRelease>", self.processar_codigo_pagamento)
        # Quando digitar o valor recebido, calcula o troco em tempo real
        self.entry_recebido.bind("<KeyRelease>", self.calcular_troco_real)
        # Tecla Enter na janela confirma a operação
        self.bind("<Return>", lambda e: self.validar_e_concluir())

    def processar_codigo_pagamento(self, event):
        codigo = self.entry_codigo.get().strip()
        
        if codigo in self.REGRAS_PAGAMENTO:
            regra = self.REGRAS_PAGAMENTO[codigo]
            
            # Atualiza o campo de descrição desabilitado
            self.entry_descricao.configure(state="normal")
            self.entry_descricao.delete(0, 'end')
            self.entry_descricao.insert(0, regra["nome"])
            self.entry_descricao.configure(state="disabled")

            if regra["pede_valor"]:
                # É Dinheiro/Cheque: Libera para digitação e limpa
                self.entry_recebido.configure(state="normal", fg_color="#2b2b2b")
                self.entry_recebido.delete(0, 'end')
                self.entry_recebido.focus()
            else:
                # É Cartão/Pix: Autopreeche o valor total e trava
                self.entry_recebido.configure(state="normal")
                self.entry_recebido.delete(0, 'end')
                self.entry_recebido.insert(0, f"{self.total_venda:.2f}")
                self.entry_recebido.configure(state="disabled", fg_color="#1a1a1a")
                
                self.lbl_troco.configure(text="TROCO: R$ 0,00", text_color="#e67e22")
                self.btn_confirmar.focus()
        else:
            # Código inválido limpa os campos auxiliares
            self.entry_descricao.configure(state="normal")
            self.entry_descricao.delete(0, 'end')
            self.entry_descricao.insert(0, "CÓDIGO INVÁLIDO")
            self.entry_descricao.configure(state="disabled")
            self.entry_recebido.delete(0, 'end')
            self.entry_recebido.configure(state="disabled", fg_color="#1a1a1a")

    def calcular_troco_real(self, event):
        try:
            valor_texto = self.entry_recebido.get().replace(',', '.')
            if not valor_texto: return
            
            valor_pago = float(valor_texto)
            troco = valor_pago - self.total_venda
            
            if troco >= 0:
                self.lbl_troco.configure(text=f"TROCO: R$ {troco:.2f}".replace('.', ','), text_color="#27ae60")
            else:
                self.lbl_troco.configure(text="VALOR INSUFICIENTE", text_color="#e74c3c")
        except ValueError:
            self.lbl_troco.configure(text="VALOR INVÁLIDO", text_color="#e74c3c")

    def validar_e_concluir(self):
        codigo = self.entry_codigo.get().strip()
        if codigo not in self.REGRAS_PAGAMENTO:
            return

        try:
            valor_pago = float(self.entry_recebido.get().replace(',', '.')) if self.entry_recebido.get() else 0.0
            if self.REGRAS_PAGAMENTO[codigo]["pede_valor"] and valor_pago < self.total_venda:
                return # Impede finalizar se faltar dinheiro
            
            troco = max(0.0, valor_pago - self.total_venda)
            
            # Retorna as informações tratadas para o MainPDV salvar no banco
            self.ao_confirmar(id_forma=int(codigo), troco=troco)
            self.destroy() # Fecha o modal
        except ValueError:
            pass