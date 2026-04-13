import customtkinter as ctk
import psycopg2
from utils.db_config import DB_CONFIG
from ui.components.edit_modal import EditModal
from tkinter import messagebox

class ListProd(ctk.CTkFrame):
    """Componente de interface que exibe a listagem de produtos do estoque em formato de tabela."""
    
    def __init__(self, master, db_connection=None, **kwargs):
        """Inicializa o frame da lista de produtos e configura a conexão com o banco."""
        super().__init__(master, **kwargs)
        self.db = db_connection
        self.configure(fg_color="transparent")
        self.setup_ui()

        self.search_time = None

    def setup_ui(self):
        """Responsável pela construção visual da estrutura da tabela."""
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(10, 20))
        
        self.label_titulo = ctk.CTkLabel(
            self.header_frame, text="Lista de Estoque", 
            font=ctk.CTkFont(family="Arial", size=32, weight="bold")
        )
        self.label_titulo.pack(side="left", anchor="w")

        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=30, pady=(0, 10))

        """ Barra para pesquisa de produtos """
        self.entry_busca = ctk.CTkEntry(
            self.search_frame, 
            placeholder_text="Pesquisar produto pelo nome...",
            width=400,
            height=35
        )
        self.entry_busca.pack(side="left", padx=(0, 10))
        self.entry_busca.bind("<Return>", lambda event: self.carregar_produtos_bd())

        self.btn_buscar = ctk.CTkButton(
            self.search_frame, 
            text="Buscar", 
            width=80,
            height=35,
            command=self.carregar_produtos_bd
        )
        self.btn_buscar.pack(side="left", padx=5)

        # Container da Tabela com Scroll
        self.tabela_frame = ctk.CTkScrollableFrame(
            self, fg_color="#2b2b2b", corner_radius=15,
            border_width=1, border_color="#3d3d3d"
        )
        self.tabela_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # Inicia o carregamento dos dados do banco
        self.carregar_produtos_bd()

    def carregar_produtos_bd(self):
        """Busca os produtos no banco de dados filtrando pelo nome e renderiza na interface."""
        
        # 1. Limpa a tabela para evitar duplicatas em atualizações
        for child in self.tabela_frame.winfo_children():
            child.destroy()

        # 2. Pega o termo de busca da barra de pesquisa
        termo_busca = self.entry_busca.get().strip()

        # 3. Configura a proporção das 6 colunas
        self.tabela_frame.grid_columnconfigure((0, 2, 3), weight=1, uniform="col")
        self.tabela_frame.grid_columnconfigure((1, 4), weight=3, uniform="col")
        self.tabela_frame.grid_columnconfigure(5, weight=2, uniform="col")

        # Cabeçalho da Tabela
        colunas = ["ID", "Nome", "Preço", "Qtd", "Categoria", "Ações"]
        for i, col in enumerate(colunas):
            lbl = ctk.CTkLabel(self.tabela_frame, text=col, font=("Arial", 14, "bold"), text_color="gray")
            lbl.grid(row=0, column=i, pady=15, sticky="nsew")

        # 4. Conexão e Busca no PostgreSQL
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # LÓGICA DE FILTRO: Se houver busca, usa ILIKE. Se não, traz tudo ativo.
            if termo_busca == "":
                query = "SELECT id, nome, preco, quantidade, categoria FROM produtos WHERE ativo = TRUE ORDER BY nome ASC"
                params = None
            else:
                # O % ao redor do termo permite buscar qualquer parte do nome
                query = "SELECT id, nome, preco, quantidade, categoria FROM produtos WHERE ativo = TRUE AND nome ILIKE %s ORDER BY nome ASC"
                params = (f"%{termo_busca}%",)

            cur.execute(query, params)
            produtos_reais = cur.fetchall()

            # 5. Loop para criar as linhas da tabela
            for i, (p_id, p_nome, p_preco, p_qtd, p_cat) in enumerate(produtos_reais):
                dados_p = {"id": p_id, "nome": p_nome, "preco": p_preco, "qtd": p_qtd, "categoria": p_cat}
                
                row_idx = i + 1
                cor_fundo = "#333333" if row_idx % 2 == 0 else "transparent" 
                
                row_frame = ctk.CTkFrame(self.tabela_frame, fg_color=cor_fundo, corner_radius=0)
                row_frame.grid(row=row_idx, column=0, columnspan=6, sticky="ew")
                
                row_frame.grid_columnconfigure((0, 2, 3), weight=1, uniform="col")
                row_frame.grid_columnconfigure((1, 4), weight=3, uniform="col")
                row_frame.grid_columnconfigure(5, weight=2, uniform="col")

                ctk.CTkLabel(row_frame, text=str(p_id)).grid(row=0, column=0, pady=10)
                ctk.CTkLabel(row_frame, text=p_nome, anchor="w").grid(row=0, column=1, pady=10, padx=20, sticky="w")
                ctk.CTkLabel(row_frame, text=f"R$ {p_preco:.2f}".replace('.', ',')).grid(row=0, column=2, pady=10)
                ctk.CTkLabel(row_frame, text=str(p_qtd)).grid(row=0, column=3, pady=10)
                ctk.CTkLabel(row_frame, text=p_cat).grid(row=0, column=4, pady=10)
                
                actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                actions_frame.grid(row=0, column=5, sticky="nsew")
                btn_container = ctk.CTkFrame(actions_frame, fg_color="transparent")
                btn_container.pack(expand=True)
                
                ctk.CTkButton(btn_container, text="Editar", width=40, cursor="hand2", 
                             command=lambda p=dados_p: self.abrir_edicao(p)).pack(side="left", padx=2)
                
                ctk.CTkButton(btn_container, text="Deletar", width=40, fg_color="#e74c3c", 
                             hover_color="#c0392b", cursor="hand2",
                             command=lambda id_p=p_id: self.deletar_produto(id_p)).pack(side="left", padx=2)

            cur.close()
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")
        finally:
            if conn:
                conn.close()

    def abrir_edicao(self, produto):
        self.modal = EditModal(
            master=self.winfo_toplevel(), 
            produto_data=produto, 
            on_save_callback=self.salvar_edicao_banco
        )

    def salvar_edicao_banco(self, novos_dados):
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            query = """
                UPDATE produtos 
                SET nome = %s, preco = %s, quantidade = %s, categoria = %s 
                WHERE id = %s
            """
            
            valores = (
                novos_dados['nome'],
                float(str(novos_dados['preco']).replace(',', '.')),
                int(novos_dados['qtd']),
                novos_dados['categoria'],
                novos_dados['id']
            )

            cur.execute(query, valores)
            conn.commit()
            
            cur.close()
            messagebox.showinfo("Sucesso", "Produto atualizado com sucesso!")
            self.carregar_produtos_bd()

        except Exception as e:
            if conn:
                conn.rollback()
            messagebox.showerror("Erro", f"Não foi possível atualizar: {e}")
        finally:
            if conn:
                conn.close()

    def deletar_produto(self, id_produto):
        """Executa a exclusão do produto no banco de dados após confirmação."""
        # 1. Janela de confirmação para evitar cliques acidentais
        confirmacao = messagebox.askyesno(
            "Confirmar Exclusão", 
            f"Deseja realmente excluir o produto (ID: {id_produto})?\nEsta ação não pode ser desfeita!"
        )

        if confirmacao:
            conn = None
            try:
                # 2. Conecta ao PostgreSQL
                conn = psycopg2.connect(**DB_CONFIG)
                cur = conn.cursor()

                # 3. Executa o comando DELETE
                query = "UPDATE produtos SET ativo = FALSE WHERE id = %s"
                cur.execute(query, (id_produto,))

                # 4. Grava a alteração
                conn.commit()
                cur.close()

                messagebox.showinfo("Sucesso", "Produto removido do estoque!")

                # 5. Atualiza a tabela na tela
                self.carregar_produtos_bd()

            except Exception as e:
                if conn:
                    conn.rollback()
                messagebox.showerror("Erro", f"Erro ao tentar deletar o produto: {e}")
            finally:
                if conn:
                    conn.close()