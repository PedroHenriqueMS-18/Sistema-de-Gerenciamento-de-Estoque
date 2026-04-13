import customtkinter as ctk
import psycopg2
from utils.db_config import DB_CONFIG
from tkinter import messagebox

"""Janela modal (pop-up) para o cadastro de novos produtos no sistema SGE."""
class PopUpCadastro(ctk.CTkToplevel):
    """Inicializa o pop-up, configurando dimensões, título e aplicando o bloqueio (modal) na janela principal."""
    def __init__(self, master, ao_salvar):
        super().__init__(master)
    
        self.ao_salvar = ao_salvar # Função para atualizar a lista de produtos na tela principal
        
        self.title("SGE - Cadastrar Novo Produto")
        self.geometry("680x500")
        self.resizable(False, False)
        
        # Faz o pop-up ficar na frente
        self.transient(master)
        self.grab_set()
        
        self.setup_ui()

    """Constrói e organiza todos os elementos visuais (rótulos, campos de entrada e botões) do formulário."""
    def setup_ui(self):
        # Título Principal (Igual ao seu print do Editar)
        self.label_titulo = ctk.CTkLabel(self, text="Cadastrar Produto", font=("Arial", 28, "bold"))
        self.label_titulo.pack(pady=(30, 5))
        
        self.label_sub = ctk.CTkLabel(self, text="Preencha os dados do novo item", font=("Arial", 12), text_color="gray")
        self.label_sub.pack(pady=(0, 20))

        # Container Principal (Dois frames lado a lado para organizar)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=40)

        # Coluna da Esquerda
        self.frame_esq = ctk.CTkFrame(self.container, corner_radius=15)
        self.frame_esq.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.label_nome = ctk.CTkLabel(self.frame_esq, text="Nome do Produto")
        self.label_nome.pack(pady=(15, 0), padx=20, anchor="w")
        self.entry_nome = ctk.CTkEntry(self.frame_esq, width=220, height=40)
        self.entry_nome.pack(pady=(5, 15), padx=20)

        self.label_preco = ctk.CTkLabel(self.frame_esq, text="Preço (R$)")
        self.label_preco.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_preco = ctk.CTkEntry(self.frame_esq, width=220, height=40)
        self.entry_preco.pack(pady=(5, 20), padx=20)

        # Coluna da Direita
        self.frame_dir = ctk.CTkFrame(self.container, corner_radius=15)
        self.frame_dir.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.label_qtd = ctk.CTkLabel(self.frame_dir, text="Qtd em Estoque")
        self.label_qtd.pack(pady=(15, 0), padx=20, anchor="w")
        self.entry_qtd = ctk.CTkEntry(self.frame_dir, width=220, height=40)
        self.entry_qtd.pack(pady=(5, 15), padx=20)

        self.label_cat = ctk.CTkLabel(self.frame_dir, text="Categoria")
        self.label_cat.pack(pady=(5, 0), padx=20, anchor="w")
        self.combo_cat = ctk.CTkOptionMenu(self.frame_dir, values=["Alimentos", "Bebidas", "Limpeza", "Higiene"], width=220, height=40)
        self.combo_cat.pack(pady=(5, 20), padx=20)

        # Botão Salvar (Verde)
        self.btn_salvar = ctk.CTkButton(self, text="CADASTRAR", fg_color="#27ae60", hover_color="#219150", 
                                        height=45, font=("Arial", 14, "bold"), command=self.salvar_produto)
        self.btn_salvar.pack(pady=30, padx=50, fill="x")

    """Coleta os dados inseridos, valida as informações e executa a inserção do produto no banco de dados."""
    def salvar_produto(self):
        # Aqui pegamos os dados e enviamos para o banco (SQL INSERT)
        nome = self.entry_nome.get()
        preco = self.entry_preco.get()
        qtd = self.entry_qtd.get()
        category = self.combo_cat.get()

        if not nome or not preco or not qtd or not category:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return

        try:
            preco_formatado = float(preco.replace(',', '.')) 
            qtd_formatada = int(qtd)
        except ValueError:
            messagebox.showwarning("Aviso", "Preço e Quantidade devem ser números válidos!")
            return
        
        conn = None

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            query = "INSERT INTO produtos (nome, preco, quantidade, categoria) VALUES (%s, %s, %s, %s)"
            cur.execute(query, (nome, preco_formatado, qtd_formatada, category))

            conn.commit()
            cur.close()

            messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")

            if self.ao_salvar:
                self.ao_salvar()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro no banco: {e}")

        finally:
            if conn:
                conn.close()