import customtkinter as ctk

class EditModal(ctk.CTkToplevel):
    """Janela modal para edição de dados de produtos com interface em duas colunas."""
    
    def __init__(self, master, produto_data, on_save_callback, **kwargs):
        """Inicializa a janela modal, configura o foco e bloqueia a janela principal."""
        super().__init__(master, **kwargs)
        
        self.title(f"Editar Produto (ID: {produto_data['id']})")
        self.geometry("600x500")
        self.after(0, lambda: self.focus_force())
        self.grab_set()

        self.produto_id = produto_data['id']
        self.on_save = on_save_callback

        self.setup_ui(produto_data)

    def setup_ui(self, data):
        """Constrói a interface visual com campos de entrada preenchidos e botões de ação."""
        self.configure(fg_color="#1a1c1e")

        ctk.CTkLabel(self, text=f"Editar Produto (ID: {self.produto_id})", 
                     font=("Arial", 24, "bold")).pack(pady=(30, 5), padx=40, anchor="w")
        ctk.CTkLabel(self, text="Altere os dados abaixo", 
                     font=("Arial", 14), text_color="gray").pack(pady=(0, 20), padx=40, anchor="w")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="x", side="top", padx=40, pady=10)

        self.col_left = ctk.CTkFrame(self.container, fg_color="#242629", corner_radius=15, border_width=1, border_color="#313437")
        self.col_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(self.col_left, text="Nome do Produto", font=("Arial", 12, "bold")).pack(pady=(5, 0), padx=15, anchor="w")
        self.ent_nome = ctk.CTkEntry(self.col_left, height=40)
        self.ent_nome.insert(0, data['nome'])
        self.ent_nome.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(self.col_left, text="Preço", font=("Arial", 12, "bold")).pack(pady=(5, 0), padx=15, anchor="w")
        self.ent_preco = ctk.CTkEntry(self.col_left, height=40)
        self.ent_preco.insert(0, data['preco'])
        self.ent_preco.pack(fill="x", padx=15, pady=10)

        self.col_right = ctk.CTkFrame(self.container, fg_color="#242629", corner_radius=15, border_width=1, border_color="#313437")
        self.col_right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(self.col_right, text="Qtd em Estoque", font=("Arial", 12, "bold")).pack(pady=(5, 0), padx=15, anchor="w")
        self.ent_qtd = ctk.CTkEntry(self.col_right, height=40)
        self.ent_qtd.insert(0, data['qtd'])
        self.ent_qtd.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(self.col_right, text="Categoria", font=("Arial", 12, "bold")).pack(pady=(5, 0), padx=15, anchor="w")
        self.cat_menu = ctk.CTkOptionMenu(self.col_right, values=["Alimentos", "Bebidas", "Limpeza"], height=40)
        self.cat_menu.pack(fill="x", padx=15, pady=10)

        self.btn_atualizar = ctk.CTkButton(
            self, text="ATUALIZAR", 
            fg_color="#f39c12", hover_color="#e67e22",
            font=("Arial", 16, "bold"), height=45,
            command=self.salvar_clicado
        )
        self.btn_atualizar.pack(pady=30, padx=40, anchor="e")

    def salvar_clicado(self):
        """Coleta os dados dos campos, executa o callback de salvamento e fecha o modal."""
        novos_dados = {
            "id": self.produto_id,
            "nome": self.ent_nome.get(),
            "preco": self.ent_preco.get(),
            "qtd": self.ent_qtd.get(),
            "categoria": self.cat_menu.get()
        }
        self.on_save(novos_dados)
        self.destroy()

# if __name__ == "__main__":
#     # Dados fakes para não dar erro de variável inexistente
#     root = ctk.CTk()
#     root.withdraw()
#     dados = {"id": 0, "nome": "", "preco": "", "qtd": ""}
    
#     # Inicia o modal sem master só para ver as cores e botões
    
#     app = EditModal(master=None, produto_data=dados, on_save_callback=lambda x: print(x))
#     root.mainloop()