import customtkinter as ctk
from tkinter import messagebox
from utils.user_service import atualizar_usuario_db, inativar_usuario_db, reativar_usuario_db

class UserManagerModal(ctk.CTkToplevel):
    def __init__(self, master, usuario_data, callback_atualizar, id_usario_logado):
        super().__init__(master)
        self.title(f"SGE Manager - Gestão de Funcionário")
        self.geometry("550x650") # Aumentei um pouco a altura para caber o CPF
        
        # Garantindo que os IDs sejam comparados como inteiros para evitar erro de tipo
        self.usuario_original = usuario_data
        self.id_logado = int(id_usario_logado)
        self.callback_atualizar = callback_atualizar
        
        self.niveis_map_reverso = {"Administrador": 1, "Operador": 2, "Vendedor": 3}
        self.niveis_map = {1: "Administrador", 2: "Operador", 3: "Vendedor"}
        
        self.grab_set() 
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        
        # Row 0: Título
        ctk.CTkLabel(
            self, text="Gerenciamento de Funcionário", 
            font=ctk.CTkFont(family="Arial", size=22, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=25)

        self.entries = {}
        campos = [
            ("ID do Usuário", "id"),
            ("Nome Completo", "nome"),
            ("Login / Usuário", "login"),
            ("CPF", "cpf") # O CPF agora está na lista e será desenhado
        ]

        # Loop que desenha os campos automaticamente (Rows 1 a 4)
        for i, (label_text, chave) in enumerate(campos):
            row_idx = i + 1
            ctk.CTkLabel(self, text=f"{label_text}:", font=("Arial", 13)).grid(row=row_idx, column=0, padx=25, pady=10, sticky="e")
            
            entry = ctk.CTkEntry(self, width=280, height=35)
            valor = str(self.usuario_original.get(chave, ""))
            
            entry.insert(0, valor)
            entry.configure(state="disabled", border_color="#3d3d3d")
            entry.grid(row=row_idx, column=1, padx=25, pady=10, sticky="w")
            self.entries[chave] = entry

        # --- LINHA DINÂMICA: A partir daqui, usamos o tamanho da lista de campos ---
        current_row = len(campos) + 1 # Atualmente será Row 5

        # --- CAMPO DE NÍVEL (OptionMenu) ---
        ctk.CTkLabel(self, text="Cargo / Nível:", font=("Arial", 13)).grid(row=current_row, column=0, padx=25, pady=10, sticky="e")
        self.var_nivel = ctk.StringVar(value=self.niveis_map.get(self.usuario_original['nivel'], "Vendedor"))
        self.menu_nivel = ctk.CTkOptionMenu(
            self, values=["Administrador", "Operador", "Vendedor"],
            variable=self.var_nivel, width=280, height=35, state="disabled"
        )
        self.menu_nivel.grid(row=current_row, column=1, padx=25, pady=10, sticky="w")

        # --- FRAME DE AÇÕES (Botões Salvar/Cancelar) ---
        current_row += 1 # Row 6
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

        # --- BOTÃO DE STATUS (Inativar) ---
        current_row += 1 # Row 7
        is_ativo = self.usuario_original.get('ativo', True)
        id_perfil = int(self.usuario_original.get('id'))
        
        self.btn_status = ctk.CTkButton(
            self, 
            text="Inativar Funcionário" if is_ativo else "Reativar Funcionário", 
            fg_color="#e74c3c" if is_ativo else "#27ae60",
            hover_color="#c0392b" if is_ativo else "#219150",
            state="disabled",
            command=self.executar_alteracao_status
        )
        self.btn_status.grid(row=current_row, column=0, columnspan=2, pady=(10, 20))

        # Trava visual inicial se for o próprio Admin
        if id_perfil == self.id_logado:
            self.btn_status.configure(text="Auto-Inativação Bloqueada", fg_color="#555555")

    def solicitar_edicao(self):
        if messagebox.askyesno("SGE", "Habilitar edição deste funcionário?"):
            for chave, entry in self.entries.items():
                if chave != "id": 
                    entry.configure(state="normal", border_color="#3498db", fg_color="#3d3d3d")
            
            self.menu_nivel.configure(state="normal")
            self.btn_editar.configure(state="disabled", fg_color="#1e3747")
            self.btn_salvar.configure(state="normal")
            self.btn_cancelar.configure(state="normal")
            
            # Bloqueio de Segurança: Só habilita o botão de status se não for o próprio usuário
            if int(self.usuario_original['id']) != self.id_logado:
                self.btn_status.configure(state="normal")
            else:
                self.btn_status.configure(state="disabled") # Reforça o bloqueio

    def resetar_estado_padrao(self, forcar=False):
        if not forcar and self.btn_salvar.cget("state") == "normal":
             if not messagebox.askyesno("Cancelar", "Descartar alterações?"):
                 return

        for chave, entry in self.entries.items():
            entry.configure(state="disabled", border_color="#3d3d3d", fg_color="#2b2b2b")
        
        self.menu_nivel.configure(state="disabled")
        self.btn_editar.configure(state="normal", fg_color="#3498db")
        self.btn_salvar.configure(state="disabled")
        self.btn_cancelar.configure(state="disabled")
        self.btn_status.configure(state="disabled")

    def confirmar_salvamento(self):
        if messagebox.askyesno("Confirmar", "Salvar alterações do funcionário?"):
            try:
                novos_dados = {
                    "id": self.usuario_original["id"],
                    "nome": self.entries["nome"].get().strip(),
                    "login": self.entries["login"].get().strip(),
                    "cpf": self.entries["cpf"].get().strip(), # Salvando o CPF também
                    "nivel": self.niveis_map_reverso.get(self.var_nivel.get())
                }
                
                if atualizar_usuario_db(novos_dados):
                    messagebox.showinfo("Sucesso", "Funcionário atualizado!")
                    self.usuario_original.update(novos_dados)
                    self.callback_atualizar()
                    self.resetar_estado_padrao(forcar=True)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def executar_alteracao_status(self):
        is_ativo = self.usuario_original.get('ativo', True)
        acao = "INATIVAR" if is_ativo else "REATIVAR"
        
        if messagebox.askyesno("Confirmação", f"Deseja realmente {acao} este funcionário?"):
            sucesso = False
            if is_ativo:
                sucesso = inativar_usuario_db(self.usuario_original['id'])
            else:
                sucesso = reativar_usuario_db(self.usuario_original['id'])
            
            if sucesso:
                messagebox.showinfo("Sucesso", f"Funcionário {acao.lower()}ado!")
                self.callback_atualizar()
                self.destroy()