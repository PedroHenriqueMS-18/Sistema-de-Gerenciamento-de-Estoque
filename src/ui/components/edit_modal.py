import customtkinter as ctk

class EditModal(ctk.CTkToplevel):
    """Janela modal para edição de dados de produtos com interface em duas colunas."""
    
    def __init__(self, master, produto_data, on_save_callback, **kwargs):
        super().__init__(master, **kwargs)
        
        self.title(f"SGE - Editar Produto (ID: {produto_data['id']})")
        self.geometry("650x500") # Aumentei um pouco a largura para não esmagar os campos
        self.after(0, lambda: self.focus_force())
        self.grab_set()

        self.produto_id = produto_data['id']
        self.on_save = on_save_callback

        self.setup_ui(produto_data)

    def setup_ui(self, data):
        self.configure(fg_color="#1a1c1e")

        # Cabeçalho
        ctk.CTkLabel(self, text=f"Editar Produto", 
                     font=("Arial", 28, "bold")).pack(pady=(30, 5), padx=40, anchor="w")
        ctk.CTkLabel(self, text=f"ID do Produto: {self.produto_id}", 
                     font=("Arial", 14), text_color="gray").pack(pady=(0, 20), padx=40, anchor="w")

        # AJUSTE 1: O container agora usa expand=True mas SEM fill="both". 
        # Isso centraliza o bloco inteiro no meio do espaço restante do modal.
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, padx=40, pady=10)

        # Coluna da Esquerda
        self.col_left = ctk.CTkFrame(self.container, fg_color="#242629", corner_radius=15, border_width=1, border_color="#313437")
        # AJUSTE 2: Removi o fill="y". Agora o frame cinza só terá a altura dos widgets internos.
        self.col_left.pack(side="left", fill="both", expand=True, padx=(0, 10), anchor="n") 

        ctk.CTkLabel(self.col_left, text="Nome do Produto", font=("Arial", 12, "bold")).pack(pady=(15, 0), padx=15, anchor="w")
        self.ent_nome = ctk.CTkEntry(self.col_left, height=40, width=220) # Width fixo para manter padrão
        self.ent_nome.insert(0, data['nome'])
        self.ent_nome.pack(padx=15, pady=10)

        ctk.CTkLabel(self.col_left, text="Preço (R$)", font=("Arial", 12, "bold")).pack(pady=(5, 0), padx=15, anchor="w")
        self.ent_preco = ctk.CTkEntry(self.col_left, height=40, width=220)
        self.ent_preco.insert(0, str(data['preco']))
        self.ent_preco.pack(padx=15, pady=10)

        ctk.CTkLabel(self.col_left, text="Código EAN", font=("Arial", 12, "bold")).pack(pady=(5, 0), padx=15, anchor="w")
        self.ent_ean = ctk.CTkEntry(self.col_left, height=40, width=220)
        self.ent_ean.insert(0, data.get('cod_ean', '')) 
        # AJUSTE 3: O último pady define onde o frame cinza acaba.
        self.ent_ean.pack(padx=15, pady=(0, 30))

        # Coluna da Direita
        self.col_right = ctk.CTkFrame(self.container, fg_color="#242629", corner_radius=15, border_width=1, border_color="#313437")
        # AJUSTE 4: Removi o fill="y" aqui também.
        self.col_right.pack(side="left", fill="both", expand=True, padx=(10, 0), anchor="n")

        ctk.CTkLabel(self.col_right, text="Qtd em Estoque", font=("Arial", 12, "bold")).pack(pady=(15, 0), padx=15, anchor="w")
        self.ent_qtd = ctk.CTkEntry(self.col_right, height=40, width=220)
        self.ent_qtd.insert(0, str(data['qtd']))
        self.ent_qtd.pack(padx=15, pady=10)

        ctk.CTkLabel(self.col_right, text="Categoria", font=("Arial", 12, "bold")).pack(pady=(5, 0), padx=15, anchor="w")
        self.cat_menu = ctk.CTkOptionMenu(self.col_right, values=["Alimentos", "Bebidas", "Limpeza", "Higiene"], height=40, width=220)
        self.cat_menu.set(data['categoria'])
        self.cat_menu.pack(padx=15, pady=10)

        # Botão Atualizar
        self.btn_atualizar = ctk.CTkButton(
            self.col_right, 
            text="SALVAR ALTERAÇÕES", 
            fg_color="#f39c12", hover_color="#e67e22",
            font=("Arial", 14, "bold"), height=45, width=220,
            command=self.salvar_clicado
        )
        # AJUSTE 5: Pady final de 20 para fechar o frame igual à coluna da esquerda.
        self.btn_atualizar.pack(padx=15, pady=(40, 30))

    def salvar_clicado(self):
        novos_dados = {
            "id": self.produto_id,
            "nome": self.ent_nome.get(),
            "preco": self.ent_preco.get(),
            "qtd": self.ent_qtd.get(),
            "categoria": self.cat_menu.get(),
            "cod_ean": self.ent_ean.get()
        }
        self.on_save(novos_dados)
        self.destroy()