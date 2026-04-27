import customtkinter as ctk
import psycopg2
from utils.db_config import DB_CONFIG
from tkinter import messagebox
# Importamos a função de busca que vamos usar
from utils.fornec_service import buscar_fornecedores_db

class PopUpCadastro(ctk.CTkToplevel):
    def __init__(self, master, ao_salvar):
        super().__init__(master)
        self.ao_salvar = ao_salvar 
        self.title("SGE - Cadastrar Novo Produto")
        self.geometry("680x580") # Aumentei um pouco para caber o novo campo
        self.resizable(False, False)
        
        self.transient(master)
        self.grab_set()
        
        # Dicionário para mapear Nome -> ID
        self.fornecedores_map = {}
        self.setup_ui()

    def setup_ui(self):
        # ... (Mantive seu título e container igual)
        self.label_titulo = ctk.CTkLabel(self, text="Cadastrar Produto", font=("Arial", 28, "bold"))
        self.label_titulo.pack(pady=(30, 5))
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=40)

        # --- COLUNA ESQUERDA ---
        self.frame_esq = ctk.CTkFrame(self.container, corner_radius=15)
        self.frame_esq.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # (Seus campos de Nome, Preço e EAN aqui...)
        self.label_nome = ctk.CTkLabel(self.frame_esq, text="Nome do Produto")
        self.label_nome.pack(pady=(15, 0), padx=20, anchor="w")
        self.entry_nome = ctk.CTkEntry(self.frame_esq, width=220, height=40)
        self.entry_nome.pack(pady=(5, 10), padx=20)

        self.label_preco = ctk.CTkLabel(self.frame_esq, text="Preço (R$)")
        self.label_preco.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_preco = ctk.CTkEntry(self.frame_esq, width=220, height=40)
        self.entry_preco.pack(pady=(5, 10), padx=20)
        
        self.label_ean = ctk.CTkLabel(self.frame_esq, text="Codigo EAN")
        self.label_ean.pack(pady=(5, 0), padx=20, anchor="w")
        self.entry_ean = ctk.CTkEntry(self.frame_esq, width=220, height=40)
        self.entry_ean.pack(pady=(5, 20), padx=20)

        # --- COLUNA DIREITA ---
        self.frame_dir = ctk.CTkFrame(self.container, corner_radius=15)
        self.frame_dir.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.label_qtd = ctk.CTkLabel(self.frame_dir, text="Qtd em Estoque")
        self.label_qtd.pack(pady=(15, 0), padx=20, anchor="w")
        self.entry_qtd = ctk.CTkEntry(self.frame_dir, width=220, height=40)
        self.entry_qtd.pack(pady=(5, 10), padx=20)

        self.label_cat = ctk.CTkLabel(self.frame_dir, text="Categoria")
        self.label_cat.pack(pady=(5, 0), padx=20, anchor="w")
        self.combo_cat = ctk.CTkOptionMenu(self.frame_dir, values=["Alimentos", "Bebidas", "Limpeza", "Higiene"], width=220, height=40)
        self.combo_cat.pack(pady=(5, 10), padx=20)

        # --- NOVO CAMPO: FORNECEDOR ---
        self.label_fornec = ctk.CTkLabel(self.frame_dir, text="Fornecedor")
        self.label_fornec.pack(pady=(5, 0), padx=20, anchor="w")
        
        # Carregamos os fornecedores do banco
        fornecs = buscar_fornecedores_db(mostrar_inativos=0)
        nomes_fornecs = ["Selecione..."]
        for f in fornecs:
            self.fornecedores_map[f[1]] = f[0] # f[1] = Nome, f[0] = ID
            nomes_fornecs.append(f[1])

        self.combo_fornec = ctk.CTkOptionMenu(self.frame_dir, values=nomes_fornecs, width=220, height=40)
        self.combo_fornec.pack(pady=(5, 20), padx=20)

        self.btn_salvar = ctk.CTkButton(self, text="CADASTRAR", fg_color="#27ae60", hover_color="#219150", 
                                        height=45, font=("Arial", 14, "bold"), command=self.salvar_produto)
        self.btn_salvar.pack(pady=(10, 20), padx=60, fill="x")

    """Coleta os dados inseridos, valida as informações e executa a inserção do produto no banco de dados."""
    def salvar_produto(self):
        nome = self.entry_nome.get().strip()
        preco = self.entry_preco.get().strip()
        qtd = self.entry_qtd.get().strip()
        category = self.combo_cat.get()
        codigo_ean = self.entry_ean.get().strip()
    
        # PEGAR O FORNECEDOR
        nome_fornec = self.combo_fornec.get()

        # Validação extra para o fornecedor
        if not codigo_ean or not nome or not preco or not qtd or nome_fornec == "Selecione...":
            messagebox.showwarning("Aviso", "Preencha todos os campos, incluindo o fornecedor!")
            return

        # Busca o ID real do fornecedor no mapa que criamos no setup_ui
        fornec_id = self.fornecedores_map.get(nome_fornec)

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

        # 1. INSERT incluindo o fornecedor_id
            query = """
                INSERT INTO produtos (nome, preco, quantidade, categoria, cod_ean, fornecedor_id) 
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """
            cur.execute(query, (nome, preco_formatado, qtd_formatada, category, codigo_ean, fornec_id))
        
            novo_id = cur.fetchone()[0]

            # 2. Log de Auditoria
            from utils.logger import registrar_log
            from utils.auth import UsuarioSessao

            detalhe_log = (f"O funcionário {UsuarioSessao.nome} cadastrou o produto: {nome} | "
                       f"EAN: {codigo_ean} | Fornecedor: {nome_fornec}")

            registrar_log(
                cursor=cur,
                acao="CADASTRO",
                tabela="produtos",
                registro_id=novo_id,
                detalhes=detalhe_log
            )

            conn.commit()
            cur.close()
            messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")

            if self.ao_salvar:
                self.ao_salvar()
            self.destroy()

        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro", f"Erro no banco: {e}")
        finally:
            if conn: conn.close()