import customtkinter as ctk
from tkinter import messagebox
from utils.product_service import atualizar_produto_db, inativar_produto_db, reativar_produto_bd
from utils.fornec_service import buscar_fornecedores_db # Importante!

class ProductManagerModal(ctk.CTkToplevel):
    def __init__(self, master, produto_data, callback_atualizar):
        super().__init__(master)
        self.title(f"SGE Manager - {produto_data['nome']}")
        self.geometry("550x700") # Aumentei um pouco a altura para o novo campo
        
        self.produto_original = produto_data
        self.callback_atualizar = callback_atualizar
        
        # Dicionário para mapear Nome -> ID
        self.fornecedores_map = {}
        
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

        # 1. Gerar campos automáticos (Rows 1 a 6)
        for i, (label_text, chave) in enumerate(campos):
            row = i + 1
            ctk.CTkLabel(self, text=f"{label_text}:", font=("Arial", 13)).grid(row=row, column=0, padx=25, pady=10, sticky="e")
            
            entry = ctk.CTkEntry(self, width=280, height=35)
            
            raw_val = self.produto_original.get(chave, "")
            valor = str(raw_val) if raw_val is not None else ""
            
            if chave == "preco" and raw_val:
                try: valor = f"{float(raw_val):.2f}".replace('.', ',')
                except: pass
            
            entry.insert(0, valor)
            entry.configure(state="disabled", border_color="#3d3d3d")
            entry.grid(row=row, column=1, padx=25, pady=10, sticky="w")
            self.entries[chave] = entry

        # 2. Campo de Fornecedor (Row 7)
        row_fornec = 7
        ctk.CTkLabel(self, text="Fornecedor:", font=("Arial", 13)).grid(row=row_fornec, column=0, padx=25, pady=10, sticky="e")
        
        # Busca fornecedores ativos para o combo
        fornecs_lista = buscar_fornecedores_db(mostrar_inativos=0)
        nomes_fornecs = []
        for f in fornecs_lista:
            self.fornecedores_map[f[1]] = f[0] # Nome Fantasia -> ID
            nomes_fornecs.append(f[1])

        self.combo_fornec = ctk.CTkOptionMenu(self, values=nomes_fornecs, width=280, height=35)
        
        # Define o fornecedor que já estava salvo (precisa vir no dicionário produto_data)
        fornec_atual = self.produto_original.get('fornecedor_nome', "Selecione...")
        self.combo_fornec.set(fornec_atual)
        self.combo_fornec.configure(state="disabled")
        self.combo_fornec.grid(row=row_fornec, column=1, padx=25, pady=10, sticky="w")

        # --- FRAME DE AÇÕES ---
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=8, column=0, columnspan=2, pady=20)

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
            self.actions_frame, text="Cancelar Edição", 
            fg_color="#e67e22", hover_color="#d35400",
            state="disabled", command=self.resetar_estado_padrao
        )
        self.btn_cancelar.pack(side="left", padx=10)

        # --- BOTÃO DE STATUS ---
        status_texto = "Inativar Produto" if self.produto_original['ativo'] else "Reativar Produto"
        status_cor = "#e74c3c" if self.produto_original['ativo'] else "#27ae60"
        status_hover = "#c0392b" if self.produto_original['ativo'] else "#219150"
        
        self.btn_status = ctk.CTkButton(
            self, text=status_texto, 
            fg_color=status_cor, hover_color=status_hover,
            state="disabled",
            command=self.executar_inativacao if self.produto_original['ativo'] else self.executar_ativacao
        )
        self.btn_status.grid(row=9, column=0, columnspan=2, pady=(10, 20))

    def solicitar_edicao(self):
        if messagebox.askyesno("SGE Manager", "Deseja habilitar os campos para edição?"):
            for chave, entry in self.entries.items():
                if chave != "id":
                    entry.configure(state="normal", border_color="#3498db", fg_color="#3d3d3d")
            
            # Habilita também o ComboBox do Fornecedor
            self.combo_fornec.configure(state="normal")
            
            self.btn_editar.configure(state="disabled", fg_color="#1e3747")
            self.btn_salvar.configure(state="normal")
            self.btn_cancelar.configure(state="normal")
            self.btn_status.configure(state="normal")

    def resetar_estado_padrao(self, forcar=False):
        if not forcar and self.btn_salvar.cget("state") == "normal":
             if not messagebox.askyesno("Cancelar", "Descartar alterações não salvas?"):
                 return

        for chave, entry in self.entries.items():
            entry.configure(state="disabled", border_color="#3d3d3d", fg_color="#2b2b2b")
        
        self.combo_fornec.configure(state="disabled")
        self.btn_editar.configure(state="normal", fg_color="#3498db")
        self.btn_salvar.configure(state="disabled")
        self.btn_cancelar.configure(state="disabled")
        self.btn_status.configure(state="disabled")

    def confirmar_salvamento(self):
        if messagebox.askyesno("Confirmar", "Deseja salvar as alterações no banco de dados?"):
            try:
                # Busca o ID do fornecedor selecionado no mapa
                nome_selecionado = self.combo_fornec.get()
                id_fornec = self.fornecedores_map.get(nome_selecionado)

                novos_dados = {
                    "id": self.produto_original["id"],
                    "ean": self.entries["ean"].get().strip(),
                    "nome": self.entries["nome"].get().strip(),
                    "preco": float(self.entries["preco"].get().replace(',', '.')),
                    "qtd": int(self.entries["qtd"].get()),
                    "categoria": self.entries["categoria"].get(),
                    "fornecedor_id": id_fornec # Novo dado enviado ao Service!
                }
                
                if atualizar_produto_db(novos_dados):
                    messagebox.showinfo("Sucesso", "Produto atualizado com sucesso!")
                    self.callback_atualizar()
                    self.produto_original.update(novos_dados)
                    self.produto_original['fornecedor_nome'] = nome_selecionado
                    self.resetar_estado_padrao(forcar=True)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao processar: {e}")

    def executar_inativacao(self):
        if messagebox.askyesno("Confirmação", "Deseja realmente INATIVAR o produto?"):
            if inativar_produto_db(self.produto_original['id']):
                messagebox.showinfo("Sucesso", "Produto inativado!")
                self.callback_atualizar()
                self.destroy()

    def executar_ativacao(self):
        if messagebox.askyesno("Confirmação", "Deseja REATIVAR o produto?"):
            if reativar_produto_bd(self.produto_original['id']):
                messagebox.showinfo("Sucesso", "Produto ativado com sucesso!")
                self.callback_atualizar()
                self.destroy()