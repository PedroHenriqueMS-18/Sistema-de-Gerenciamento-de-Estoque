import customtkinter as ctk
from tkinter import messagebox
from utils.fornec_service import atualizar_fornecedor_db, alterar_status_fornecedor_db

class FornecEditModal(ctk.CTkToplevel):
    def __init__(self, master, fornecedor_data, callback_atualizar):
        super().__init__(master)
        self.title("SGE Manager - Gestão de Fornecedor")
        self.geometry("600x700")
        
        self.fornecedor_original = fornecedor_data
        self.callback_atualizar = callback_atualizar
        
        self.grab_set() 
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        
        # Row 0: Título
        ctk.CTkLabel(
            self, text="Gerenciamento de Fornecedor", 
            font=ctk.CTkFont(family="Arial", size=22, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=25)

        self.entries = {}
        # Lista de campos baseada na estrutura da tabela 'fornecedores'
        campos = [
            ("ID do Registro", "id"),
            ("Nome Fantasia", "nome_fantasia"),
            ("Razão Social", "razao_social"),
            ("CNPJ", "cnpj"),
            ("Telefone", "telefone"),
            ("E-mail", "email"),
            ("Endereço", "endereco")
        ]

        # Loop de desenho dos campos
        for i, (label_text, chave) in enumerate(campos):
            row_idx = i + 1
            ctk.CTkLabel(self, text=f"{label_text}:", font=("Arial", 13)).grid(row=row_idx, column=0, padx=25, pady=8, sticky="e")
            
            entry = ctk.CTkEntry(self, width=320, height=35)
            valor = str(self.fornecedor_original.get(chave, ""))
            
            entry.insert(0, valor if valor != "None" else "")
            # Começa desabilitado por padrão
            entry.configure(state="disabled", border_color="#3d3d3d")
            entry.grid(row=row_idx, column=1, padx=25, pady=8, sticky="w")
            self.entries[chave] = entry

        current_row = len(campos) + 1

        # --- FRAME DE AÇÕES ---
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=current_row, column=0, columnspan=2, pady=30)

        self.btn_editar = ctk.CTkButton(
            self.actions_frame, text="Habilitar Edição", 
            fg_color="#3498db", hover_color="#2980b9",
            command=self.solicitar_edicao
        )
        self.btn_editar.pack(side="left", padx=10)

        self.btn_salvar = ctk.CTkButton(
            self.actions_frame, text="Salvar", 
            fg_color="#2ecc71", hover_color="#27ae60",
            state="disabled", command=self.confirmar_salvamento
        )
        self.btn_salvar.pack(side="left", padx=10)

        self.btn_cancelar = ctk.CTkButton(
            self.actions_frame, text="Cancelar", 
            fg_color="#e67e22", hover_color="#d35400",
            state="disabled", command=lambda: self.resetar_estado_padrao()
        )
        self.btn_cancelar.pack(side="left", padx=10)

        # --- BOTÃO DE STATUS ---
        current_row += 1
        is_ativo = self.fornecedor_original.get('ativo', True)
        
        self.btn_status = ctk.CTkButton(
            self, 
            text="Inativar Fornecedor" if is_ativo else "Reativar Fornecedor", 
            fg_color="#e74c3c" if is_ativo else "#27ae60",
            hover_color="#c0392b" if is_ativo else "#219150",
            state="disabled",
            command=self.executar_alteracao_status
        )
        self.btn_status.grid(row=current_row, column=0, columnspan=2, pady=(10, 20))

    def solicitar_edicao(self):
        if messagebox.askyesno("SGE", "Habilitar edição deste fornecedor?"):
            for chave, entry in self.entries.items():
                if chave != "id": # ID nunca se edita
                    entry.configure(state="normal", border_color="#3498db", fg_color="#3d3d3d")
            
            self.btn_editar.configure(state="disabled", fg_color="#1e3747")
            self.btn_salvar.configure(state="normal")
            self.btn_cancelar.configure(state="normal")
            self.btn_status.configure(state="normal")

    def resetar_estado_padrao(self, forcar=False):
        if not forcar and self.btn_salvar.cget("state") == "normal":
             if not messagebox.askyesno("Cancelar", "Descartar alterações?"):
                 return

        for chave, entry in self.entries.items():
            entry.configure(state="disabled", border_color="#3d3d3d", fg_color="#2b2b2b")
        
        self.btn_editar.configure(state="normal", fg_color="#3498db")
        self.btn_salvar.configure(state="disabled")
        self.btn_cancelar.configure(state="disabled")
        self.btn_status.configure(state="disabled")

    def confirmar_salvamento(self):
        if messagebox.askyesno("Confirmar", "Salvar alterações do fornecedor?"):
            try:
                novos_dados = {
                    "id": self.fornecedor_original["id"],
                    "nome_fantasia": self.entries["nome_fantasia"].get().strip(),
                    "razao_social": self.entries["razao_social"].get().strip(),
                    "cnpj": self.entries["cnpj"].get().strip(),
                    "telefone": self.entries["telefone"].get().strip(),
                    "email": self.entries["email"].get().strip(),
                    "endereco": self.entries["endereco"].get().strip()
                }
                
                if atualizar_fornecedor_db(novos_dados):
                    messagebox.showinfo("Sucesso", "Dados do fornecedor atualizados!")
                    self.fornecedor_original.update(novos_dados)
                    self.callback_atualizar()
                    self.resetar_estado_padrao(forcar=True)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def executar_alteracao_status(self):
        is_ativo = self.fornecedor_original.get('ativo', True)
        novo_status = not is_ativo
        acao = "INATIVAR" if is_ativo else "REATIVAR"
        
        if messagebox.askyesno("Confirmação", f"Deseja realmente {acao} este fornecedor?"):
            if alterar_status_fornecedor_db(self.fornecedor_original['id'], novo_status):
                messagebox.showinfo("Sucesso", f"Fornecedor {acao.lower()}ado!")
                self.callback_atualizar()
                self.destroy()