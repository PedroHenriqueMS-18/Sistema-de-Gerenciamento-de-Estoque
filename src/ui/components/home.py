import customtkinter as ctk
import psycopg2
from utils.db_config import DB_CONFIG
from ui.components.cadastro_prod import PopUpCadastro

class Home(ctk.CTkFrame):
    def __init__(self, master, db_connection=None, funcao_estoque=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.db = db_connection
        self.ir_para_estoque = funcao_estoque
        self.configure(fg_color="transparent")

        self.setup_ui()
        
        # BUSCA O VALOR REAL ASSIM QUE A TELA INICIA
        self.carregar_total_produtos()

    def setup_ui(self):
        # ... (seu código de UI permanece o mesmo até o label_valor_prod)
        self.label_welcome = ctk.CTkLabel(self, text="Bem-vindo ao SGE Manager", font=("Arial", 32, "bold"))
        self.label_welcome.pack(pady=(40, 50), padx=50, anchor="w")

        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=50)

        self.card_produtos = ctk.CTkFrame(self.cards_frame, fg_color="#1a1c1e", height=250, corner_radius=20, border_width=2, border_color="#313437")
        self.card_produtos.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.card_produtos.pack_propagate(False)

        ctk.CTkLabel(self.card_produtos, text="Produtos Cadastrados", font=("Arial", 18), text_color="gray").pack(pady=(40, 5))
        
        # Iniciamos com "..." para indicar que está carregando
        self.label_valor_prod = ctk.CTkLabel(self.card_produtos, text="...", font=("Arial", 64, "bold"), text_color="white")
        self.label_valor_prod.pack(pady=(10, 40))

        # ... (restante dos botões e frames de ação)
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.pack(fill="x", padx=50, pady=50)

        self.btn_new_prod = ctk.CTkButton(self.actions_frame, text="CADASTRAR NOVO PRODUTO", fg_color="#2ecc71", 
                                         command=self.abrir_popup_cadastro, height=50, font=("Arial", 16, "bold"))
        self.btn_new_prod.pack(side="left", expand=True, padx=(0, 10), fill="x")

        self.btn_view_estoque = ctk.CTkButton(self.actions_frame, text="VER ESTOQUE ABERTO", fg_color="#3498db", 
                                             command=self.ir_para_estoque, height=50, font=("Arial", 16, "bold"))
        self.btn_view_estoque.pack(side="left", expand=True, padx=(10, 0), fill="x")

    def carregar_total_produtos(self):
        """Busca no banco de dados a quantidade total de itens cadastrados."""
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Query mágica que conta as linhas da tabela
            cur.execute("SELECT COUNT(*) FROM produtos WHERE ativo = TRUE")
            total = cur.fetchone()[0] # Pega o primeiro valor da primeira linha resultante
            
            self.label_valor_prod.configure(text=str(total))
            cur.close()
        except Exception as e:
            print(f"Erro ao carregar contador: {e}")
            self.label_valor_prod.configure(text="Err")
        finally:
            if conn:
                conn.close()

    def abrir_popup_cadastro(self):
        self.popup = PopUpCadastro(
            master=self.winfo_toplevel(), 
            ao_salvar=self.atualizar_contador_dashboard
        )

    def atualizar_contador_dashboard(self):
        """Ação disparada após o cadastro de sucesso no Pop-up."""
        print("Novo produto detectado. Atualizando contador via Banco de Dados...")
        # Em vez de somar manualmente, chamamos a fonte da verdade: o Banco!
        self.carregar_total_produtos()

    