import customtkinter as ctk
from datetime import datetime

class TelaPDV(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.bg_color = "#1a1a1a"
        self.accent_color = "#3498db" 
        self.success_color = "#27ae60" 
        self.botoes_atalho = []
        
        self.configure(fg_color=self.bg_color)
        self.setup_ui()

    def setup_ui(self):
        # --- 1. HEADER (Data, Operador, Status Caixa) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", height=50, corner_radius=0)
        self.header_frame.pack(fill="x", side="top", padx=0, pady=0)
        
        data_atual = datetime.now().strftime("%d/%m/%Y")
        self.lbl_data = ctk.CTkLabel(self.header_frame, text=f"DATA: {data_atual}", font=("Arial", 16, "bold"))
        self.lbl_data.pack(side="left", padx=20)
        
        self.lbl_operador = ctk.CTkLabel(self.header_frame, text="OPERADOR: ", font=("Arial", 16))
        self.lbl_operador.pack(side="left", padx=50)
        
        self.status_indicador = ctk.CTkLabel(self.header_frame, text="● CAIXA: ", font=("Arial", 16, "bold"))
        self.status_indicador.pack(side="right", padx=20)

        # --- 2. ÁREA DE TÍTULO E PRODUTO SELECIONADO ---
        self.title_label = ctk.CTkLabel(self, text="PDV - PONTO DE VENDA", font=("Arial", 32, "bold"))
        self.title_label.pack(pady=(20, 5)) # Reduzido de 10 para 5 para ganhar espaço
        
        self.product_focus_frame = ctk.CTkFrame(self, fg_color="#333333", height=60)
        self.product_focus_frame.pack(fill="x", padx=40, pady=5)
        self.lbl_foco_produto = ctk.CTkLabel(self.product_focus_frame, text="Produto Selecionado: NENHUM", font=("Arial", 24, "bold"))
        self.lbl_foco_produto.pack(pady=10)

        # --- 3. CAMPO DE ENTRADA (CÓDIGO DE BARRAS) ---
        self.entry_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.entry_frame.pack(fill="x", padx=40, pady=5)
        
        self.lbl_ean = ctk.CTkLabel(self.entry_frame, text="CÓDIGO DE BARRAS (F1):", font=("Arial", 18, "bold"))
        self.lbl_ean.pack(side="left", padx=(0, 10))
        
        self.entry_barcode = ctk.CTkEntry(self.entry_frame, placeholder_text="Bipa o código ou digita...", height=50, font=("Arial", 18), fg_color="#2b2b2b")
        self.entry_barcode.pack(side="left", fill="x", expand=True)
        
        self.btn_buscar = ctk.CTkButton(self.entry_frame, text="BUSCAR (Enter)", fg_color=self.accent_color, hover_color="#2980b9", height=50, width=150, font=("Arial", 16, "bold"))
        self.btn_buscar.pack(side="left", padx=(10, 0))

        # --- NOVO: DISPLAY DE DETALHES (TRAVADO PARA NÃO ROUBAR ESPAÇO) ---
        # height=90 e pack_propagate(False) garantem que o frame não mude de tamanho
        self.details_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", height=90)
        self.details_frame.pack(fill="x", padx=40, pady=5)
        self.details_frame.pack_propagate(False) 

        # Sub-frame Quantidade
        self.sub_frame_qtd = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.sub_frame_qtd.pack(side="left", expand=True, fill="both")
        ctk.CTkLabel(self.sub_frame_qtd, text="QUANTIDADE", font=("Arial", 11, "bold"), text_color="gray").pack(pady=(10, 0))
        self.lbl_qtd_display = ctk.CTkLabel(self.sub_frame_qtd, text="1", font=("Arial", 26, "bold"), text_color=self.accent_color)
        self.lbl_qtd_display.pack(pady=(0, 5))

        # Sub-frame Valor Unitário
        self.sub_frame_unit = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.sub_frame_unit.pack(side="left", expand=True, fill="both")
        ctk.CTkLabel(self.sub_frame_unit, text="VALOR UNITÁRIO", font=("Arial", 11, "bold"), text_color="gray").pack(pady=(10, 0))
        self.lbl_unit_display = ctk.CTkLabel(self.sub_frame_unit, text="R$ 0,00", font=("Arial", 26, "bold"), text_color=self.success_color)
        self.lbl_unit_display.pack(pady=(0, 5))

        # --- 4. TABELA DE ITENS (Scrollable) ---
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.table_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        self.render_table_headers()

        # --- 5. TOTALIZADOR ---
        self.total_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.total_frame.pack(fill="x", padx=40, pady=10)
        
        self.lbl_total = ctk.CTkLabel(self.total_frame, text="TOTAL: R$ 0,00", font=("Arial", 42, "bold"))
        self.lbl_total.pack(side="right")

        # --- 6. BARRA DE ATALHOS (BOTTOM) ---
        self.shortcuts_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.shortcuts_frame.pack(fill="x", side="bottom", padx=40, pady=(10, 30))
        
        self.create_shortcut_buttons()

    def render_table_headers(self):
        headers = ["ÍT.", "CÓDIGO", "DESCRIÇÃO DO PRODUTO", "QTD", "VL. UNIT.", "SUBTOTAL"]
        self.table_weights = [1, 3, 5, 1, 2, 2]
        
        # Voltamos o master para self.table_frame para ele seguir o mesmo scroll das linhas
        header_row = ctk.CTkFrame(self.table_frame, fg_color="#3d3d3d", corner_radius=0)
        header_row.pack(fill="x", side="top", pady=(0, 5))
        
        for i, text in enumerate(headers):
            lbl = ctk.CTkLabel(
                header_row, 
                text=text, 
                font=("Arial", 12, "bold"), 
                text_color="gray",
                anchor="center"
            )
            lbl.grid(row=0, column=i, sticky="nsew", pady=5)
            # O segredo do alinhamento vertical é o uniform="column_group"
            header_row.grid_columnconfigure(i, weight=self.table_weights[i], uniform="column_group")
            
    def adicionar_linha_produto(self, item_num, ean, nome, qtd, valor_unit):
        subtotal = qtd * valor_unit
        cor_linha = "#333333" if item_num % 2 == 0 else "transparent"
        
        row_frame = ctk.CTkFrame(self.table_frame, fg_color=cor_linha, corner_radius=0)
        row_frame.pack(fill="x", pady=0)

        dados = [
            f"{item_num:03d}",
            str(ean),
            str(nome).upper(),
            f"{qtd:.3f}",
            f"{valor_unit:.2f}",
            f"{subtotal:.2f}"
        ]

        for i, texto in enumerate(dados):
            lbl = ctk.CTkLabel(
                row_frame, 
                text=texto, 
                font=("Arial", 14), 
                text_color="white",
                anchor="center"
            )
            lbl.grid(row=0, column=i, sticky="nsew", pady=8)
            # IMPORTANTE: O uniform deve ser o mesmo nome usado no header ("column_group")
            row_frame.grid_columnconfigure(i, weight=self.table_weights[i], uniform="column_group")

        self.update_idletasks()
        self.table_frame._parent_canvas.yview_moveto(1.0)

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
            btn = ctk.CTkButton(self.shortcuts_frame, text=text, fg_color="transparent", 
                                border_width=2, border_color=color, hover_color="#333333", 
                                height=60, font=("Arial", 12, "bold"))
            btn.grid(row=0, column=i, padx=5, sticky="ew")
            self.shortcuts_frame.grid_columnconfigure(i, weight=1)
            self.botoes_atalho.append(btn)

    def atualizar_status_caixa(self, aberto=False):
        if aberto:
            self.status_indicador.configure(text="● CAIXA: ABERTO", text_color=self.success_color)
            self.entry_barcode.configure(state="normal", fg_color="#2b2b2b")
            self.entry_barcode.focus() 
            self.btn_buscar.configure(state="normal")
            for btn in self.botoes_atalho:
                btn.configure(state="normal")
        else:
            self.status_indicador.configure(text="● CAIXA: FECHADO", text_color="#e74c3c")
            self.lbl_foco_produto.configure(text="Produto Selecionado: NENHUM")
            self.lbl_total.configure(text="TOTAL: R$ 0,00")
            self.lbl_qtd_display.configure(text="1")
            self.lbl_unit_display.configure(text="R$ 0,00")
            
            self.entry_barcode.delete(0, 'end')
            self.entry_barcode.configure(state="disabled", fg_color="#1a1a1a")
            self.btn_buscar.configure(state="disabled")
            for btn in self.botoes_atalho:
                btn.configure(state="disabled")