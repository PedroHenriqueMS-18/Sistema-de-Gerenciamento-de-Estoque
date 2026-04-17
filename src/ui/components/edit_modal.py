import customtkinter as ctk
from tkinter import messagebox
from utils.product_service import atualizar_produto_db, inativar_produto_db, reativar_produto_bd

class ProductManagerModal(ctk.CTkToplevel):
    def __init__(self, master, produto_data, callback_atualizar):
        super().__init__(master)
        self.title(f"SGE Manager - {produto_data['nome']}")
        self.geometry("550x650")
        
        self.produto_original = produto_data
        self.callback_atualizar = callback_atualizar
        
        self.grab_set() 
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            self, text="Gerenciamento de Produto", 
            font=ctk.CTkFont(family="Arial", size=22, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=25)

        self.entries = {}
        campos = [
            ("ID do Produto", "id"),
            ("Código EAN", "ean"),
            ("Nome do Produto", "nome"),
            ("Preço de Venda", "preco"),
            ("Quantidade", "qtd"),
            ("Categoria", "categoria")
        ]

        for i, (label_text, chave) in enumerate(campos):
            row = i + 1
            ctk.CTkLabel(self, text=f"{label_text}:", font=("Arial", 13)).grid(row=row, column=0, padx=25, pady=10, sticky="e")
            
            entry = ctk.CTkEntry(self, width=280, height=35)
            
            # Trata valores None e formata preço
            raw_val = self.produto_original.get(chave, "")
            valor = str(raw_val) if raw_val is not None else ""
            if chave == "preco" and raw_val:
                try: valor = f"{float(raw_val):.2f}".replace('.', ',')
                except: pass
            
            entry.insert(0, valor)
            entry.configure(state="disabled", border_color="#3d3d3d")
            entry.grid(row=row, column=1, padx=25, pady=10, sticky="w")
            self.entries[chave] = entry

        # --- FRAME DE AÇÕES ---
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=7, column=0, columnspan=2, pady=20)

        # Botão EDITAR (Único ativo ao abrir)
        self.btn_editar = ctk.CTkButton(
            self.actions_frame, text="Habilitar Edição", 
            fg_color="#3498db", hover_color="#2980b9",
            text_color_disabled="white", # Mantém o texto visível
            command=self.solicitar_edicao
        )
        self.btn_editar.pack(side="left", padx=10)

        # Botão SALVAR (Inativo ao abrir)
        self.btn_salvar = ctk.CTkButton(
            self.actions_frame, text="Salvar", 
            fg_color="#2ecc71", hover_color="#27ae60",
            state="disabled", text_color_disabled="#a0a0a0",
            command=self.confirmar_salvamento
        )
        self.btn_salvar.pack(side="left", padx=10)

        # Botão CANCELAR (Inativo ao abrir - Nome mudado de Sair para Cancelar)
        self.btn_cancelar = ctk.CTkButton(
            self.actions_frame, text="Cancelar Edição", 
            fg_color="#e67e22", hover_color="#d35400",
            state="disabled", text_color_disabled="#a0a0a0",
            command=self.resetar_estado_padrao
        )
        self.btn_cancelar.pack(side="left", padx=10)

        # --- BOTÃO DE STATUS (Inativo ao abrir) ---
        if self.produto_original['ativo']:
            self.btn_status = ctk.CTkButton(
                self, text="Inativar Produto", 
                fg_color="#e74c3c", hover_color="#c0392b",
                state="disabled", text_color_disabled="#a0a0a0",
                command=self.executar_inativacao
            )
        else:
            self.btn_status = ctk.CTkButton(
                self, text="Reativar Produto", 
                fg_color="#27ae60", hover_color="#219150",
                state="disabled", text_color_disabled="#a0a0a0",
                command=self.executar_ativacao
            )
        self.btn_status.grid(row=8, column=0, columnspan=2, pady=(10, 20))

    def solicitar_edicao(self):
        """Libera os campos e ativa os botões de ação."""
        if messagebox.askyesno("SGE Manager", "Deseja habilitar os campos para edição?"):
            for chave, entry in self.entries.items():
                if chave != "id":
                    entry.configure(state="normal", border_color="#3498db", fg_color="#3d3d3d")
            
            self.btn_editar.configure(state="disabled", fg_color="#1e3747") # Escurece o botão de editar
            self.btn_salvar.configure(state="normal")
            self.btn_cancelar.configure(state="normal")
            self.btn_status.configure(state="normal")

    def resetar_estado_padrao(self, forcar=False):
        """Bloqueia tudo e volta ao estado original sem fechar a janela."""
        
        # O PULO DO GATO: Se 'forcar' for False, ele checa se deve avisar o usuário.
        # Se for True (após salvar), ele ignora o aviso e limpa tudo.
        if not forcar and self.btn_salvar.cget("state") == "normal":
             if not messagebox.askyesno("Cancelar", "As alterações não salvas serão perdidas. Continuar?"):
                 return

        # Tranca todos os campos de novo
        for chave, entry in self.entries.items():
            entry.configure(state="disabled", border_color="#3d3d3d", fg_color="#2b2b2b")
        
        # Restaura os botões para o estado de "apenas leitura"
        self.btn_editar.configure(state="normal", fg_color="#3498db")
        self.btn_salvar.configure(state="disabled")
        self.btn_cancelar.configure(state="disabled")
        self.btn_status.configure(state="disabled")

    def confirmar_salvamento(self):
        if messagebox.askyesno("Confirmar", "Deseja salvar as alterações no banco de dados?"):
            try:
                novos_dados = {
                    "id": self.produto_original["id"],
                    "ean": self.entries["ean"].get(),
                    "nome": self.entries["nome"].get(),
                    "preco": float(self.entries["preco"].get().replace(',', '.')),
                    "qtd": int(self.entries["qtd"].get()),
                    "categoria": self.entries["categoria"].get()
                }
                
                if atualizar_produto_db(novos_dados):
                    messagebox.showinfo("Sucesso", "Produto atualizado com sucesso!")
                    self.callback_atualizar()
                    
                    # Atualiza o objeto local para o 'Cancelar' não resetar para o nome antigo
                    self.produto_original.update(novos_dados)
                    
                    # CHAMADA SILENCIOSA: Aqui ele reseta sem perguntar nada
                    self.resetar_estado_padrao(forcar=True) 
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao processar: {e}")

    def executar_inativacao(self):
        if messagebox.askyesno("Confirmação", f"Deseja realmente INATIVAR o produto?"):
            if inativar_produto_db(self.produto_original['id']):
                messagebox.showinfo("Sucesso", "Produto inativado!")
                self.callback_atualizar()
                self.destroy() # Inativar geralmente encerra a gestão rápida do item

    def executar_ativacao(self):
        if messagebox.askyesno("Confirmação", f"Deseja REATIVAR o produto?"):
            if reativar_produto_bd(self.produto_original['id']):
                messagebox.showinfo("Sucesso", "Produto ativado com sucesso!")
                self.callback_atualizar()
                self.destroy()