import customtkinter as ctk
from tkinter import messagebox
# Importamos o cliente do Supabase e o registrador de logs
from utils.auth import supabase_client, UsuarioSessao
from utils.logger import registrar_log
from utils.fornec_service import buscar_fornecedores_db

class PopUpCadastro(ctk.CTkToplevel):
    def __init__(self, master, ao_salvar):
        super().__init__(master)
        self.ao_salvar = ao_salvar 
        self.title("SGE - Cadastrar Novo Produto")
        self.geometry("680x580")
        self.resizable(False, False)
        
        self.transient(master)
        self.grab_set()
        
        # Dicionário para mapear Nome -> ID
        self.fornecedores_map = {}
        self.setup_ui()

    def setup_ui(self):
        self.label_titulo = ctk.CTkLabel(self, text="Cadastrar Produto", font=("Arial", 28, "bold"))
        self.label_titulo.pack(pady=(30, 5))
        
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=40)

        # --- COLUNA ESQUERDA ---
        self.frame_esq = ctk.CTkFrame(self.container, corner_radius=15)
        self.frame_esq.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

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

        # --- CAMPO: FORNECEDOR ---
        self.label_fornec = ctk.CTkLabel(self.frame_dir, text="Fornecedor")
        self.label_fornec.pack(pady=(5, 0), padx=20, anchor="w")
        
        # Carregamos os fornecedores do banco na nuvem
        fornecs = buscar_fornecedores_db(mostrar_inativos=0)
        nomes_fornecs = ["Selecione..."]
        for f in fornecs:
            self.fornecedores_map[f[1]] = f[0] # f[1] = Nome Fantasia, f[0] = ID
            nomes_fornecs.append(f[1])

        self.combo_fornec = ctk.CTkOptionMenu(self.frame_dir, values=nomes_fornecs, width=220, height=40)
        self.combo_fornec.pack(pady=(5, 20), padx=20)

        self.btn_salvar = ctk.CTkButton(self, text="CADASTRAR", fg_color="#27ae60", hover_color="#219150", 
                                        height=45, font=("Arial", 14, "bold"), command=self.salvar_produto)
        self.btn_salvar.pack(pady=(10, 20), padx=60, fill="x")

    def salvar_produto(self):
        """Coleta, valida e executa o INSERT direto na nuvem do Supabase."""
        nome = self.entry_nome.get().strip()
        preco = self.entry_preco.get().strip()
        qtd = self.entry_qtd.get().strip()
        category = self.combo_cat.get()
        codigo_ean = self.entry_ean.get().strip()
        nome_fornec = self.combo_fornec.get()

        # 1. VALIDAÇÃO DE CAMPOS VAZIOS
        if not codigo_ean or not nome or not preco or not qtd or nome_fornec == "Selecione...":
            messagebox.showwarning("Aviso", "Preencha todos os campos, incluindo o fornecedor!")
            return

        # Busca o ID real do fornecedor no mapa local
        fornec_id = self.fornecedores_map.get(nome_fornec)

        # 2. TRATAMENTO DE TIPAGEM DOS NÚMEROS
        try:
            preco_formatado = float(preco.replace(',', '.')) 
            qtd_formatada = int(qtd)
        except ValueError:
            messagebox.showwarning("Aviso", "Preço e Quantidade devem ser números válidos!")
            return
    
        try:
            # 3. MONTAGEM DO DICIONÁRIO (PAYLOAD) COM AS COLUNAS DO BANCO
            valores_insert = {
                "nome": nome,
                "preco": preco_formatado,
                "quantidade": qtd_formatada,
                "categoria": category,
                "cod_ean": codigo_ean,
                "fornecedor_id": int(fornec_id) if fornec_id is not None else None,
                "ativo": True # Todo produto novo entra ativo por padrão
            }

            # 4. DISPARA O INSERT USANDO O MÉTODO DA CLASSE DO SUPABASE
            # Lembra que estudamos? .table().insert().execute() para fazer a ação!
            response = supabase_client.table("produtos").insert(valores_insert).execute()
        
            if response is None:
                messagebox.showerror("Erro", "O banco de dados não respondeu ao cadastro.")
                return

            # 5. ISOLAMENTO DO NOVO ID GERADO (Índice zero da lista .data)
            novo_id = None
            if response.data:
                novo_id = response.data[0].get("id")

            # 6. LOG DE AUDITORIA (Sem cursor, enviamos None)
            detalhe_log = (f"O funcionário {UsuarioSessao.nome} cadastrou o produto: {nome} | "
                           f"EAN: {codigo_ean} | Fornecedor: {nome_fornec}")

            try:
                registrar_log(
                    cursor=None,
                    acao="CADASTRO",
                    tabela="produtos",
                    registro_id=novo_id,
                    detalhes=detalhe_log
                )
            except Exception as log_err:
                print(f"⚠️ Erro ao registrar log de auditoria: {log_err}")

            # 7. SUCESSO E REFRESH AUTOMÁTICO
            messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")

            if self.ao_salvar:
                self.ao_salvar() # Executa o callback de atualizar a tabela principal
                
            self.destroy() # Fecha a janela limpa

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar no Supabase: {e}")