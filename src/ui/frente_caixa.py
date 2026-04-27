import customtkinter as ctk
from datetime import datetime

class TelaPDV(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configurações de cores baseadas na imagem
        self.bg_color = "#1a1a1a"
        self.accent_color = "#3498db" # Azul do botão buscar
        self.success_color = "#27ae60" # Verde do status
        
        self.configure(fg_color=self.bg_color)
        self.setup_ui()

    def setup_ui(self):
        # --- 1. HEADER (Data, Operador, Status Caixa) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", height=50, corner_radius=0)
        self.header_frame.pack(fill="x", side="top", padx=0, pady=0)
        
        data_atual = datetime.now().strftime("%d/%m/%Y")
        self.lbl_data = ctk.CTkLabel(self.header_frame, text=f"DATA: {data_atual}", font=("Arial", 16, "bold"))
        self.lbl_data.pack(side="left", padx=20)
        
        self.lbl_operador = ctk.CTkLabel(self.header_frame, text="OPERADOR: Maria Silva", font=("Arial", 16))
        self.lbl_operador.pack(side="left", padx=50)
        
        self.status_indicador = ctk.CTkLabel(self.header_frame, text="● CAIXA: ABERTO", text_color=self.success_color, font=("Arial", 16, "bold"))
        self.status_indicador.pack(side="right", padx=20)

        # --- 2. ÁREA DE TÍTULO E PRODUTO SELECIONADO ---
        self.title_label = ctk.CTkLabel(self, text="PDV - PONTO DE VENDA", font=("Arial", 32, "bold"))
        self.title_label.pack(pady=(20, 10))
        
        self.product_focus_frame = ctk.CTkFrame(self, fg_color="#333333", height=60)
        self.product_focus_frame.pack(fill="x", padx=40, pady=10)
        self.lbl_foco_produto = ctk.CTkLabel(self.product_focus_frame, text="Produto Selecionado: Coca-Cola 2L", font=("Arial", 24, "bold"))
        self.lbl_foco_produto.pack(pady=10)

        # --- 3. CAMPO DE ENTRADA (CÓDIGO DE BARRAS) ---
        self.entry_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.entry_frame.pack(fill="x", padx=40, pady=10)
        
        self.lbl_ean = ctk.CTkLabel(self.entry_frame, text="CÓDIGO DE BARRAS (F1):", font=("Arial", 18, "bold"))
        self.lbl_ean.pack(side="left", padx=(0, 10))
        
        self.entry_barcode = ctk.CTkEntry(self.entry_frame, placeholder_text="Bipa o código ou digita...", height=50, font=("Arial", 18), fg_color="#2b2b2b")
        self.entry_barcode.pack(side="left", fill="x", expand=True)
        
        self.btn_buscar = ctk.CTkButton(self.entry_frame, text="BUSCAR (Enter)", fg_color=self.accent_color, hover_color="#2980b9", height=50, width=150, font=("Arial", 16, "bold"))
        self.btn_buscar.pack(side="left", padx=(10, 0))

        # --- 4. TABELA DE ITENS (Scrollable) ---
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.table_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        # Cabeçalhos da Tabela
        self.render_table_headers()

        # --- 5. TOTALIZADOR ---
        self.total_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.total_frame.pack(fill="x", padx=40, pady=10)
        
        self.lbl_total = ctk.CTkLabel(self.total_frame, text="TOTAL: R$ 51,50", font=("Arial", 42, "bold"))
        self.lbl_total.pack(side="right")

        # --- 6. BARRA DE ATALHOS (BOTTOM) ---
        self.shortcuts_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.shortcuts_frame.pack(fill="x", side="bottom", padx=40, pady=(10, 30))
        
        self.create_shortcut_buttons()

    def render_table_headers(self):
        headers = ["ÍT.", "CÓDIGO", "DESCRIÇÃO DO PRODUTO", "QTD", "VL. UNIT.", "SUBTOTAL"]
        weights = [1, 3, 5, 1, 2, 2] # Pesos das colunas
        
        header_row = ctk.CTkFrame(self.table_frame, fg_color="#3d3d3d")
        header_row.pack(fill="x", pady=2)
        
        for i, text in enumerate(headers):
            lbl = ctk.CTkLabel(header_row, text=text, font=("Arial", 12, "bold"), text_color="gray")
            lbl.grid(row=0, column=i, sticky="nsew", pady=5)
            header_row.grid_columnconfigure(i, weight=weights[i])

    def create_shortcut_buttons(self):
        shortcuts = [
            ("F1\nPesquisar", self.accent_color),
            ("F2\nNova Venda", self.accent_color),
            ("F3\nCliente CPF", self.accent_color),
            ("F4\nQuantidade", self.accent_color),
            ("F5\nFinalizar/NFC-e", self.success_color),
            ("F6\nCancelar Venda", "#e74c3c"),
            ("F12\nFechar Caixa", "#c0392b")
        ]
        
        for i, (text, color) in enumerate(shortcuts):
            btn = ctk.CTkButton(self.shortcuts_frame, text=text, fg_color="transparent", border_width=2, border_color=color, hover_color="#333333", height=60, font=("Arial", 12, "bold"))
            btn.grid(row=0, column=i, padx=5, sticky="ew")
            self.shortcuts_frame.grid_columnconfigure(i, weight=1)

    def atualizar_status_caixa(self, aberto=False):
        """
        Controla o estado operacional do PDV.
        True: Caixa liberado para vendas.
        False: Interface bloqueada, aguardando abertura.
        """
        if aberto:
            # 1. VISUAL: Muda o indicador para VERDE e texto para ABERTO
            self.status_indicador.configure(
                text="● CAIXA: ABERTO", 
                text_color="#27ae60" # Verde sucesso
            )

            # 2. ENTRADA: Habilita o campo de código de barras e foca nele
            self.entry_barcode.configure(state="normal", fg_color="#2b2b2b")
            self.entry_barcode.focus() # Já deixa o cursor piscando para bipar

            # 3. BOTÕES: Habilita o botão de busca e os de atalho (F1, F2, etc.)
            self.btn_buscar.configure(state="normal")
        
            # Aqui você habilitaria seus botões de atalho da barra inferior
            # Exemplo: self.btn_f5.configure(state="normal")
        
        else:
            # 1. VISUAL: Muda o indicador para VERMELHO e texto para FECHADO
            self.status_indicador.configure(
                text="● CAIXA: FECHADO", 
                text_color="#e74c3c" # Vermelho erro/parado
            )

            # 2. LIMPEZA: Reseta os textos de feedback para o padrão inicial
            self.lbl_foco_produto.configure(text="Produto Selecionado: NENHUM")
            self.lbl_total.configure(text="TOTAL: R$ 0,00")
            
            # 3. BLOQUEIO: Desabilita a entrada de dados e limpa o campo
            self.entry_barcode.delete(0, 'end')
            self.entry_barcode.configure(state="disabled", fg_color="#1a1a1a")
            
            # 4. BOTÕES: Desabilita o botão de busca
            self.btn_buscar.configure(state="disabled")
            
            # Aqui você desabilitaria os botões de atalho
            # Exemplo: self.btn_f5.configure(state="disabled")