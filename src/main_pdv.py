import customtkinter as ctk
from ui.frente_caixa import TelaPDV
from ui.login import LoginWindow 
from utils.auth import UsuarioSessao
from ui.components.modal_abertura import ModalAbertura
from ui.components.modal_pag import ModalPagamento
from ui.components.modal_pesquisa_produto import ModalPesquisaProduto
from ui.components.modal_remocao_produto import ModalRemocaoProduto
from ui.components.modal_cliente_cpf import ModalClienteCPF
from ui.components.modal_sangria import ModalSangria
from tkinter import messagebox
from utils.pdv_service import (
    buscar_produto_por_ean,
    salvar_venda,
    abrir_sessao_caixa,
    calcular_saldo_caixa,
    registrar_movimentacao_caixa,
    gerar_comprovante_sangria
)
import sys

class MainPDV(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Estimaí - Frente de Caixa")
        self.geometry("1200x800")
        self.after(0, lambda: self.state('zoomed'))
        self.protocol("WM_DELETE_WINDOW", self.confirmar_fechamento)

        # --- VARIÁVEIS DE ESTADO ---
        self.caixa_aberto = False
        self.quantidade_atual = 1.0
        self.total_venda = 0.0
        self.itens_venda = []
        self.cpf_cliente = None  # Guardado apenas em memória; usado na impressão da notinha
        self.id_caixa_atual = None  # id da sessão em 'sessoes_caixa'; alimenta vendas e sangrias
        self.saldo_abertura = 0.0  # Valor de suprimento informado na abertura do caixa

        self.interface = TelaPDV(master=self)
        self.interface.pack(fill="both", expand=True)

        self.meus_atalhos = {
            "F1": self.abrir_pesquisa_produto,
            "F2": self.abrir_remocao_produto,
            "F3": self.abrir_cliente_cpf,
            "F4": self.abrir_sangria,
            "F5": self.finalizar_venda,
            "F6": self.cancelar_venda_atual,
            "F12": self.confirmar_fechamento
        }
        self.interface.create_shortcut_buttons(self.meus_atalhos)

        self.interface.lbl_operador.configure(text=f"OPERADOR: {UsuarioSessao.nome}")
        self.interface.atualizar_status_caixa(aberto=False)

        self.configurar_binds()
        self.after(500, self.disparar_abertura)

    def configurar_binds(self):
        self.interface.entry_barcode.bind("<Return>", self.processar_item)
        self.interface.btn_buscar.configure(command=self.processar_item)
        self.interface.entry_barcode.bind("<KeyRelease>", self.detectar_multiplicador)

        for tecla, funcao in self.meus_atalhos.items():
            self.bind_all(f"<{tecla}>", lambda e, f=funcao: f())

    def detectar_multiplicador(self, event):
        texto = self.interface.entry_barcode.get()
        if "*" in texto:
            try:
                qtd_str = texto.split("*")[0].replace(',', '.')
                qtd_val = float(qtd_str) if qtd_str else 1.0
                if qtd_val > 0:
                    self.quantidade_atual = qtd_val
                    self.interface.lbl_qtd_display.configure(text=f"{int(qtd_val) if qtd_val.is_integer() else qtd_val}")
                self.interface.entry_barcode.delete(0, 'end')
            except ValueError:
                self.interface.entry_barcode.delete(0, 'end')
                self.quantidade_atual = 1.0
                self.interface.lbl_qtd_display.configure(text="1")

    def processar_item(self, event=None):
        if not self.caixa_aberto:
            return

        ean = self.interface.entry_barcode.get().strip()
        if not ean:
            return

        produto = buscar_produto_por_ean(ean)

        if produto:
            self.adicionar_produto_a_venda(produto)
        else:
            messagebox.showwarning("Atenção", f"Código {ean} não localizado!")

        self.quantidade_atual = 1.0
        self.interface.lbl_qtd_display.configure(text="1")
        self.interface.entry_barcode.delete(0, 'end')
        self.interface.entry_barcode.focus()

    def adicionar_produto_a_venda(self, produto):
        """
        Aplica na venda atual um produto já localizado, seja pela leitura direta
        do código de barras (F1 do teclado físico/bipador) ou pela seleção feita
        no modal de pesquisa (F1 do sistema). Mantém a mesma tupla de retorno de
        'buscar_produto_por_ean': (id, cod_ean, nome, preco, quantidade).
        """
        id_prod, cod_ean, nome, preco_unit, estoque = produto
        preco_unit = float(preco_unit)

        subtotal_item = preco_unit * self.quantidade_atual
        preco_unit_exibir = f"{preco_unit:.2f}".replace('.', ',')

        self.interface.lbl_foco_produto.configure(text=f"PRODUTO: {nome}")
        self.interface.lbl_unit_display.configure(text=f"R$ {preco_unit_exibir}")

        # Registra no cache antes do desenho em tela
        self.itens_venda.append({
            "id": id_prod,
            "ean": cod_ean,
            "nome": nome,
            "qtd": self.quantidade_atual,
            "preco": preco_unit,
            "subtotal": subtotal_item
        })

        # Injeta o método 'self.excluir_item_venda' como escuta da linha
        self.interface.adicionar_linha_produto(
            item_num=len(self.itens_venda),
            ean=cod_ean,
            nome=nome,
            qtd=self.quantidade_atual,
            valor_unit=preco_unit,
            callback_excluir=self.excluir_item_venda
        )

        self.total_venda += subtotal_item
        self.interface.lbl_total.configure(text=f"TOTAL: R$ {f'{self.total_venda:.2f}'.replace('.', ',')}")

    def abrir_pesquisa_produto(self):
        """Abre o modal de pesquisa de produtos (F1) por código de barras ou nome."""
        if not self.caixa_aberto:
            messagebox.showwarning("Atenção", "Abra o caixa antes de pesquisar produtos!")
            return

        ModalPesquisaProduto(master=self, ao_selecionar=self.processar_produto_selecionado)

    def abrir_remocao_produto(self):
        """Abre o modal de remoção de produtos da venda atual (F2)."""
        if not self.caixa_aberto:
            messagebox.showwarning("Atenção", "Abra o caixa antes de remover produtos!")
            return

        if not self.itens_venda:
            messagebox.showwarning("Atenção", "Não há produtos na venda atual para remover!")
            return

        ModalRemocaoProduto(master=self, callback_remover=self.excluir_item_venda)

    def abrir_cliente_cpf(self):
        """Abre o modal de identificação do cliente por CPF (F3)."""
        if not self.caixa_aberto:
            messagebox.showwarning("Atenção", "Abra o caixa antes de identificar o cliente!")
            return

        ModalClienteCPF(master=self, cpf_atual=self.cpf_cliente, ao_salvar=self.definir_cpf_cliente)

    def abrir_sangria(self):
        """Abre o modal de Sangria de caixa (F4), já com o saldo real disponível na gaveta."""
        if not self.caixa_aberto or not self.id_caixa_atual:
            messagebox.showwarning("Atenção", "Abra o caixa antes de realizar uma sangria!")
            return

        saldo_disponivel = calcular_saldo_caixa(self.id_caixa_atual, self.saldo_abertura)
        ModalSangria(master=self, saldo_disponivel=saldo_disponivel, ao_confirmar=self.processar_sangria)

    def processar_sangria(self, valor, motivo):
        """
        Callback do modal de Sangria (F4): registra a movimentação em
        'movimentacoes_caixa' e gera o comprovante em .txt para o operador
        imprimir/anexar na gaveta.
        """
        saldo_antes = calcular_saldo_caixa(self.id_caixa_atual, self.saldo_abertura)

        sucesso, resultado = registrar_movimentacao_caixa(
            id_caixa=self.id_caixa_atual,
            id_operador=UsuarioSessao.id,
            tipo="SANGRIA",
            valor=valor,
            observacao=motivo
        )

        if not sucesso:
            messagebox.showerror("Erro", f"Não foi possível registrar a sangria: {resultado}")
            return

        id_movimentacao = resultado
        saldo_depois = saldo_antes - valor
        valor_exibir = f"{valor:.2f}".replace('.', ',')

        caminho_comprovante = gerar_comprovante_sangria(
            id_movimentacao=id_movimentacao,
            id_caixa=self.id_caixa_atual,
            operador_nome=UsuarioSessao.nome,
            valor=valor,
            observacao=motivo,
            saldo_antes=saldo_antes,
            saldo_depois=saldo_depois
        )

        if caminho_comprovante:
            messagebox.showinfo(
                "Sangria Registrada",
                f"Sangria de R$ {valor_exibir} registrada com sucesso!\n\nComprovante salvo em:\n{caminho_comprovante}"
            )
        else:
            messagebox.showinfo("Sangria Registrada", f"Sangria de R$ {valor_exibir} registrada com sucesso!")

        self.interface.entry_barcode.focus()

    def definir_cpf_cliente(self, cpf):
        """
        Callback do modal de CPF (F3). Guarda o CPF apenas em memória, vinculado
        à venda em andamento — será usado na impressão da notinha ao finalizar
        a venda (funcionalidade futura). Não é persistido no banco.
        """
        self.cpf_cliente = cpf
        self.interface.atualizar_cliente_cpf(cpf)
        self.interface.entry_barcode.focus()

    def processar_produto_selecionado(self, produto):
        """Callback do modal de pesquisa (F1): adiciona o produto escolhido à venda atual."""
        self.adicionar_produto_a_venda(produto)

        self.quantidade_atual = 1.0
        self.interface.lbl_qtd_display.configure(text="1")
        self.interface.entry_barcode.delete(0, 'end')
        self.interface.entry_barcode.focus()

    def excluir_item_venda(self, indice_alvo):
        """Remove o item do array lógico por índice e força o redesenho sequencial da tabela."""
        if indice_alvo >= len(self.itens_venda):
            return

        item = self.itens_venda[indice_alvo]
        pergunta = f"Deseja remover o item {item['nome']} da venda atual?"
        
        if messagebox.askyesno("Remover Item", pergunta):
            # Abate o subtotal do item removido do totalizador geral da venda
            self.total_venda -= item['subtotal']
            if self.total_venda < 0: 
                self.total_venda = 0.0
                
            # Remove da lista encadeada do Python
            self.itens_venda.pop(indice_alvo)
            
            self.interface.lbl_total.configure(text=f"TOTAL: R$ {f'{self.total_venda:.2f}'.replace('.', ',')}")
            
            # --- REDESENHO DA MÁQUINA DE COMPONENTES ---
            # Remove todas as linhas visuais preservando apenas os cabeçalhos fixos
            for widget in self.interface.table_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") != "#3d3d3d":
                    widget.destroy()
            
            # Re-renderiza os itens restantes reconstruindo a numeração (001, 002, 003...)
            for i, restante in enumerate(self.itens_venda):
                self.interface.adicionar_linha_produto(
                    item_num=i + 1,
                    ean=restante['ean'],
                    nome=restante['nome'],
                    qtd=restante['qtd'],
                    valor_unit=restante['preco'],
                    callback_excluir=self.excluir_item_venda
                )
            
            messagebox.showinfo("Sucesso", "Item removido com sucesso!")
            self.interface.entry_barcode.focus()

    def disparar_abertura(self):
        if not self.caixa_aberto:
            modal = ModalAbertura(master=self, ao_confirmar=self.finalizar_abertura)
            modal.focus_force()
            modal.grab_set()
        else:
            messagebox.showinfo("Aviso", "O caixa já está aberto!")

    def finalizar_abertura(self, valor):
        """
        Callback do ModalAbertura: registra a sessão em 'sessoes_caixa' no Supabase
        antes de destravar o PDV. Sem um id_caixa válido, a Sangria não pode funcionar
        (a tabela movimentacoes_caixa exige essa referência).
        """
        id_caixa = abrir_sessao_caixa(id_operador=UsuarioSessao.id, valor_abertura=valor)

        if not id_caixa:
            messagebox.showerror("Erro", "Não foi possível abrir o caixa no banco de dados. Tente novamente.")
            return False

        self.id_caixa_atual = id_caixa
        self.saldo_abertura = valor
        self.caixa_aberto = True
        self.interface.atualizar_status_caixa(aberto=True)

    def confirmar_fechamento(self):
        if messagebox.askyesno("Sair", "Deseja realmente fechar o Frente de Caixa?"):
            self.destroy()

    def finalizar_venda(self):
        if not self.itens_venda:
            messagebox.showwarning("Atenção", "Não há itens na venda!")
            return

        ModalPagamento(
            master=self, 
            total_venda=self.total_venda, 
            ao_confirmar=self.concluir_venda_banco
        )

    def concluir_venda_banco(self, id_forma, troco):
        if messagebox.askyesno("Confirmar Venda", f"Deseja realmente registrar esta venda?"):
            sucesso, resultado = salvar_venda(
                id_operador=UsuarioSessao.id,
                valor_total=self.total_venda,
                id_caixa=self.id_caixa_atual,
                lista_itens=self.itens_venda,
                status='CONCLUIDA',
                id_forma_pagamento=id_forma,
                troco=troco
            )

            if sucesso:
                messagebox.showinfo("Sucesso", f"Venda #{resultado} realizada com sucesso!")
                self.limpar_caixa_pos_venda()
            else:
                messagebox.showerror("Erro", f"Erro crítico ao salvar no banco: {resultado}")
                
    def cancelar_venda_atual(self):
        if not self.itens_venda: 
            return
        
        if messagebox.askyesno("Confirmar", "Deseja realmente CANCELAR esta venda em andamento?"):
            sucesso, resultado = salvar_venda(
                id_operador=UsuarioSessao.id,
                valor_total=self.total_venda,
                id_caixa=self.id_caixa_atual,
                lista_itens=None, 
                status='CANCELADA'
            )

            if sucesso:
                messagebox.showwarning("Aviso", f"Venda #{resultado} cancelada e registrada para auditoria.")
                self.limpar_caixa_pos_venda()

    def limpar_caixa_pos_venda(self):
        self.itens_venda = []
        self.total_venda = 0.0
        self.quantidade_atual = 1.0
        self.cpf_cliente = None
        
        self.interface.lbl_total.configure(text="TOTAL: R$ 0,00")
        self.interface.lbl_foco_produto.configure(text="Produto Selecionado: NENHUM")
        self.interface.lbl_unit_display.configure(text="R$ 0,00")
        self.interface.lbl_qtd_display.configure(text="1")
        self.interface.atualizar_cliente_cpf(None)
        
        for widget in self.interface.table_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") != "#3d3d3d":
                widget.destroy()
                
        self.interface.entry_barcode.delete(0, 'end')
        self.interface.entry_barcode.focus()

def iniciar_sistema():
    def montar_pdv():
        app_pdv = MainPDV()
        app_pdv.mainloop()
    login = LoginWindow(on_login_success=montar_pdv)
    login.mainloop()

if __name__ == "__main__":
    iniciar_sistema()