import customtkinter as ctk
# Importamos o cliente e a sessão do Supabase
from utils.auth import supabase_client, UsuarioSessao
from ui.components.cadastro_prod import PopUpCadastro
from tkinter import messagebox

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

        # --- FRAME DE AÇÕES ---
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.pack(fill="x", padx=50, pady=50)

        self.btn_new_prod = ctk.CTkButton(self.actions_frame, text="CADASTRAR NOVO PRODUTO", fg_color="#2ecc71", 
                                          command=self.abrir_popup_cadastro, height=50, font=("Arial", 16, "bold"))
        self.btn_new_prod.pack(side="left", expand=True, padx=(0, 10), fill="x")

        # Trava de Segurança visual por Nível de Usuário
        if UsuarioSessao.nivel not in [1, 2]:
            self.btn_new_prod.configure(state="disabled", fg_color="gray", text="Acesso Restrito")

        self.btn_view_estoque = ctk.CTkButton(self.actions_frame, text="VER ESTOQUE ABERTO", fg_color="#3498db", 
                                              command=self.ir_para_estoque, height=50, font=("Arial", 16, "bold"))
        self.btn_view_estoque.pack(side="left", expand=True, padx=(10, 0), fill="x")

    def carregar_total_produtos(self):
        """Busca no Supabase a quantidade total de itens ativos cadastrados."""
        try:
            # 💡 EXPLICAÇÃO DA MÁGICA:
            # Pedimos para selecionar apenas o ID (para ser super leve), mas passamos o parâmetro
            # count="exact". Isso faz o Supabase retornar a contagem real na propriedade .count
            response = supabase_client.table("produtos")\
                .select("id", count="exact")\
                .eq("ativo", True)\
                .execute()
            
            # Capturamos o número total gerado direto na nuvem
            total = response.count if response.count is not None else 0
            
            # Atualiza o imponente label na tela principal
            self.label_valor_prod.configure(text=str(total))
            
        except Exception as e:
            print(f"❌ Erro ao carregar contador do Supabase: {e}")
            self.label_valor_prod.configure(text="Err")

    def abrir_popup_cadastro(self):
        if UsuarioSessao.nivel in [1, 2]:
            self.popup = PopUpCadastro(
                master=self.winfo_toplevel(), 
                ao_salvar=self.atualizar_contador_dashboard
            )
        else:
            messagebox.showwarning("Acesso restrito", "Apenas Administradores ou Operadores podem cadastrar novos produtos.")
        
    def atualizar_contador_dashboard(self):
        """Ação disparada após o cadastro de sucesso no Pop-up."""
        print("🔄 Novo produto detectado. Atualizando contador via Supabase...")
        self.carregar_total_produtos()