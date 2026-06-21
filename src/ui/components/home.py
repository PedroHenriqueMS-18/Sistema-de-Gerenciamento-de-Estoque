import customtkinter as ctk
from datetime import datetime
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
        
        # Carrega todos os dados do dashboard vindos do Supabase
        self.atualizar_dados_dashboard()

    def setup_ui(self):
        # --- HEADER PRINCIPAL ---
        self.label_welcome = ctk.CTkLabel(self, text="Bem-vindo ao SGE Manager", font=("Arial", 28, "bold"))
        self.label_welcome.pack(pady=(30, 20), padx=50, anchor="w")

        # --- 1. FILEIRA DE CARDS (MÉTRICAS PRINCIPAIS) ---
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=50, pady=(0, 20))
        
        # Card 1: Faturamento Diário
        self.card_faturamento = ctk.CTkFrame(self.cards_frame, fg_color="#1a1c1e", height=140, corner_radius=15, border_width=1, border_color="#313437")
        self.card_faturamento.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.card_faturamento.pack_propagate(False)
        
        ctk.CTkLabel(self.card_faturamento, text="Faturamento Bruto (Hoje)", font=("Arial", 14, "bold"), text_color="#3498db").pack(pady=(20, 5), padx=20, anchor="w")
        self.label_valor_faturamento = ctk.CTkLabel(self.card_faturamento, text="R$ 0,00", font=("Arial", 32, "bold"), text_color="#2ecc71")
        self.label_valor_faturamento.pack(pady=(5, 15), padx=20, anchor="w")

        # Card 2: Produtos Cadastrados
        self.card_produtos = ctk.CTkFrame(self.cards_frame, fg_color="#1a1c1e", height=140, corner_radius=15, border_width=1, border_color="#313437")
        self.card_produtos.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.card_produtos.pack_propagate(False)

        ctk.CTkLabel(self.card_produtos, text="Produtos Cadastrados", font=("Arial", 14, "bold"), text_color="gray").pack(pady=(20, 5), padx=20, anchor="w")
        self.label_valor_prod = ctk.CTkLabel(self.card_produtos, text="...", font=("Arial", 32, "bold"), text_color="white")
        self.label_valor_prod.pack(pady=(5, 15), padx=20, anchor="w")

        # --- 2. SEÇÃO CENTRAL: RANKING DE VENDAS (MENSAL) ---
        self.rank_section_frame = ctk.CTkFrame(self, fg_color="#1a1c1e", corner_radius=15, border_width=1, border_color="#313437")
        self.rank_section_frame.pack(fill="both", expand=True, padx=50, pady=10)
        
        ctk.CTkLabel(self.rank_section_frame, text="🏆 Top 10 Produtos Mais Vendidos do Mês", font=("Arial", 18, "bold"), text_color="white").pack(pady=(20, 15), padx=25, anchor="w")
        
        # Container rolável para comportar o gráfico de barras sem estourar o layout
        self.chart_scroll_container = ctk.CTkScrollableFrame(self.rank_section_frame, fg_color="transparent")
        self.chart_scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # --- 3. FRAME DE AÇÕES (BOTTOM) ---
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.pack(fill="x", padx=50, pady=(20, 30))

        self.btn_new_prod = ctk.CTkButton(self.actions_frame, text="➕ CADASTRAR NOVO PRODUTO", fg_color="#2ecc71", hover_color="#27ae60",
                                         command=self.abrir_popup_cadastro, height=45, font=("Arial", 14, "bold"))
        self.btn_new_prod.pack(side="left", expand=True, padx=(0, 10), fill="x")

        if UsuarioSessao.nivel not in [1, 2]:
            self.btn_new_prod.configure(state="disabled", fg_color="gray", text="Acesso Restrito")

        self.btn_view_estoque = ctk.CTkButton(self.actions_frame, text="📦 VER ESTOQUE ABERTO", fg_color="#3498db", hover_color="#2980b9",
                                             command=self.ir_para_estoque, height=45, font=("Arial", 14, "bold"))
        self.btn_view_estoque.pack(side="left", expand=True, padx=(10, 0), fill="x")

    def atualizar_dados_dashboard(self):
        """Dispara todas as atualizações de dados agregados no banco."""
        self.carregar_total_produtos()
        self.carregar_faturamento_diario()
        self.carregar_top_produtos_mes()

    def carregar_total_produtos(self):
        """Busca no Supabase a quantidade total de itens ativos cadastrados."""
        try:
            response = supabase_client.table("produtos").select("id", count="exact").eq("ativo", True).execute()
            total = response.count if response.count is not None else 0
            self.label_valor_prod.configure(text=str(total))
        except Exception as e:
            print(f"❌ Erro ao carregar contador do Supabase: {e}")
            self.label_valor_prod.configure(text="Err")

    def carregar_faturamento_diario(self):
        """Calcula o faturamento bruto das vendas concluídas na data de hoje."""
        try:
            # 🔧 CORREÇÃO 1: Pega a data atual formatada exatamente como o seu tipo 'date' espera (AAAA-MM-DD)
            hoje_formatado = datetime.now().strftime("%Y-%m-%d")
            
            # Buscamos filtrando pela coluna real: 'data_venda'
            response = supabase_client.table("vendas")\
                .select("valor_total")\
                .eq("status", "CONCLUIDA")\
                .eq("data_venda", hoje_formatado)\
                .execute()
                
            total_hoje = 0.0
            if response.data:
                for venda in response.data:
                    total_hoje += float(venda.get("valor_total", 0))
            
            faturamento_formatado = f"R$ {total_hoje:.2f}".replace('.', ',')
            self.label_valor_faturamento.configure(text=faturamento_formatado)
        except Exception as e:
            print(f"❌ Erro ao calcular faturamento diário: {e}")
            self.label_valor_faturamento.configure(text="R$ --,--")

    def carregar_top_produtos_mes(self):
        """Puxa os itens vendidos no mês atual e constrói o gráfico de rank de barras."""
        try:
            for widget in self.chart_scroll_container.winfo_children():
                widget.destroy()

            # Formatamos o primeiro dia do mês atual (Ex: 2026-06-01)
            primeiro_dia_mes = datetime.now().strftime("%Y-%m-01")

            # 🔧 CORREÇÃO 2: Montamos o grande JOIN trilateral do Supabase!
            # 1. Pegamos a quantidade de 'itens_venda'
            # 2. Fazemos o join com 'produtos' para buscar o (nome)
            # 3. Fazemos o join com 'vendas' para buscar o (status, data_venda) para podermos filtrar!
            response = supabase_client.table("itens_venda")\
                .select("quantidade, produtos(nome), vendas(status, data_venda)")\
                .gte("vendas.data_venda", primeiro_dia_mes)\
                .eq("vendas.status", "CONCLUIDA")\
                .execute()

            if not response.data:
                lbl_no_data = ctk.CTkLabel(self.chart_scroll_container, text="Nenhuma venda registrada este mês ainda.", font=("Arial", 14, "italic"), text_color="gray")
                lbl_no_data.pack(pady=30)
                return

            # Agrupa e consolida as quantidades por produto na memória do Python
            consolidado = {}
            for item in response.data:
                # Extrai o nome do produto vindo do Join de produtos
                dados_prod = item.get("produtos", {})
                nome = dados_prod.get("nome", "Desconhecido").upper() if dados_prod else "DESCONHECIDO"
                
                qtd = float(item.get("quantidade", 0))
                consolidado[nome] = consolidado.get(nome, 0) + qtd

            # Se o dicionário estiver vazio (ex: vendas filtradas não tinham itens válidos)
            if not consolidado:
                lbl_no_data = ctk.CTkLabel(self.chart_scroll_container, text="Nenhuma venda concluída este mês.", font=("Arial", 14, "italic"), text_color="gray")
                lbl_no_data.pack(pady=30)
                return

            # Ordena e extrai o Top 10 mais vendidos
            top_10 = sorted(consolidado.items(), key=lambda x: x[1], reverse=True)[:10]

            max_quantidade = top_10[0][1] if top_10 else 1

            for rank, (nome_prod, qtd_total) in enumerate(top_10, start=1):
                row_item = ctk.CTkFrame(self.chart_scroll_container, fg_color="transparent")
                row_item.pack(fill="x", pady=6)

                texto_label = f"{rank}º  {nome_prod} ({int(qtd_total) if qtd_total.is_integer() else qtd_total} un)"
                lbl_info = ctk.CTkLabel(row_item, text=texto_label, font=("Arial", 13, "bold"), width=280, anchor="w", text_color="#e0e0e0")
                lbl_info.pack(side="left", padx=(10, 15))

                bar_bg_track = ctk.CTkFrame(row_item, fg_color="#2b2d30", height=16, corner_radius=8)
                bar_bg_track.pack(side="left", fill="x", expand=True)
                bar_bg_track.pack_propagate(False)

                porcentagem_largura = qtd_total / max_quantidade
                if porcentagem_largura < 0.02: 
                    porcentagem_largura = 0.02
                
                cor_barra = "#f1c40f" if rank == 1 else "#e2e2e2" if rank == 2 else "#e67e22" if rank == 3 else "#3498db"

                bar_fill = ctk.CTkFrame(bar_bg_track, fg_color=cor_barra, height=16, corner_radius=8)
                bar_fill.place(relwidth=porcentagem_largura, relx=0, rely=0)

        except Exception as e:
            print(f"❌ Erro ao processar ranking do Top 10: {e}")
            lbl_err = ctk.CTkLabel(self.chart_scroll_container, text="Erro ao carregar ranking de vendas.", text_color="#e74c3c")

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
        print("🔄 Sincronizando novos dados com o Dashboard via Supabase...")
        self.atualizar_dados_dashboard()