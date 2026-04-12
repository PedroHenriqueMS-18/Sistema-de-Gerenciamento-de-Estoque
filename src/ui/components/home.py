import customtkinter as ctk

"""Componente de interface que representa a tela inicial (Dashboard) do sistema."""
class Home(ctk.CTkFrame):
    """Inicializa o frame da Home, configura a conexão com o banco e define o fundo transparente."""
    def __init__(self, master, db_connection=None, funcao_estoque=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.db = db_connection
        self.ir_para_estoque = funcao_estoque
        self.configure(fg_color="transparent")

        self.setup_ui()

    """Responsável por construir e organizar todos os elementos visuais do Dashboard."""
    def setup_ui(self):
        """Cria e posiciona a mensagem de boas-vindas no topo da tela."""
        self.label_welcome = ctk.CTkLabel(
            self, text="Bem-vindo ao SGE Manager", 
            font=ctk.CTkFont(family="Arial", size=32, weight="bold")
        )
        self.label_welcome.pack(pady=(40, 50), padx=50, anchor="w")

        """Define o container horizontal para abrigar os cartões de métricas e estatísticas."""
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=50)

        """Constrói o cartão visual de resumo para exibir a quantidade total de produtos."""
        self.card_produtos = ctk.CTkFrame(
            self.cards_frame, 
            fg_color="#1a1c1e", 
            height=250, 
            corner_radius=20,
            border_width=2,
            border_color="#313437"
        )
        self.card_produtos.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.card_produtos.pack_propagate(False)

        """Adiciona o rótulo descritivo e o valor numérico dentro do cartão de produtos."""
        ctk.CTkLabel(self.card_produtos, text="Produtos Cadastrados", font=("Arial", 18), text_color="gray").pack(pady=(40, 5))
        
        self.label_valor_prod = ctk.CTkLabel(self.card_produtos, text="154", font=("Arial", 64, "bold"), text_color="white")
        self.label_valor_prod.pack(pady=(10, 40))

        """Cria a seção inferior destinada aos botões de acesso rápido às funcionalidades."""
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.pack(fill="x", padx=50, pady=50)

        """Configura o botão de atalho para a abertura do formulário de novo cadastro."""
        self.btn_new_prod = ctk.CTkButton(
            self.actions_frame, 
            text="CADASTRAR NOVO PRODUTO", 
            fg_color="#2ecc71",
            hover_color="#27ae60",
            font=("Arial", 16, "bold"),
            height=50,
            corner_radius=10,
            cursor="hand2"
        )
        self.btn_new_prod.pack(side="left", expand=True, padx=(0, 10), fill="x")

        """Configura o botão de atalho para visualização rápida da lista de estoque completa."""
        self.btn_view_estoque = ctk.CTkButton(
            self.actions_frame, 
            text="VER ESTOQUE ABERTO", 
            fg_color="#3498db",
            hover_color="#2980b9",
            font=("Arial", 16, "bold"),
            height=50,
            corner_radius=10,
            command=self.ir_para_estoque
        )
        self.btn_view_estoque.pack(side="left", expand=True, padx=(10, 0), fill="x")