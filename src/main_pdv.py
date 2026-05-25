import customtkinter as ctk
from ui.frente_caixa import TelaPDV
from ui.login import LoginWindow 
from utils.auth import UsuarioSessao
from ui.components.modal_abertura import ModalAbertura
from ui.components.modal_pag import ModalPagamento
from tkinter import messagebox
from utils.pdv_service import buscar_produto_por_ean, salvar_venda
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
        self.itens_venda = []  # <<< CORREÇÃO 1: Faltava inicializar esta lista aqui!

        self.interface = TelaPDV(master=self)
        self.interface.pack(fill="both", expand=True)

        self.meus_atalhos = {
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
        # 1. Binds específicos que já existiam
        # F2 para abertura (usando bind_all para garantir que funcione de qualquer lugar)
        self.bind_all("<F2>", lambda e: self.disparar_abertura())
        
        # Enter no campo de código de barras
        self.interface.entry_barcode.bind("<Return>", self.processar_item)
        
        # Botão buscar (já configurado no seu código)
        self.interface.btn_buscar.configure(command=self.processar_item)
        
        # Detectar o multiplicador (ex: 2*789...)
        self.interface.entry_barcode.bind("<KeyRelease>", self.detectar_multiplicador)

        # 2. Loop Dinâmico para os Atalhos do Dicionário (F5, F6, F12, etc.)
        # Isso evita que você precise fazer um self.bind para cada tecla manualmente.
        for tecla, funcao in self.meus_atalhos.items():
            # Usamos bind_all para que o F5 funcione mesmo se o cursor estiver no Entry
            # f=funcao garante que o loop não 'perca' a referência da função correta
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
            id_prod, cod_ean, nome, preco_unit, estoque = produto
            # Mantemos preco_unit como FLOAT para todas as contas
            preco_unit = float(preco_unit)

            # Cálculo do subtotal (Número * Número = Sucesso)
            subtotal_item = preco_unit * self.quantidade_atual
            
            # Criamos variáveis de EXIBIÇÃO (apenas para a interface)
            # Aqui já podemos colocar a vírgula brasileira!
            preco_unit_exibir = f"{preco_unit:.2f}".replace('.', ',')

            # --- ATUALIZAÇÃO DA INTERFACE ---
            self.interface.lbl_foco_produto.configure(text=f"PRODUTO: {nome}")
            # Usamos a variável de EXIBIÇÃO no label
            self.interface.lbl_unit_display.configure(text=f"R$ {preco_unit_exibir}")

            # Chama a função visual (Passamos o PREÇO PURO para ela fazer o cálculo lá dentro)
            self.interface.adicionar_linha_produto(
                item_num=len(self.itens_venda) + 1,
                ean=cod_ean,
                nome=nome,
                qtd=self.quantidade_atual,
                valor_unit=preco_unit # <-- Passa o float aqui!
            )

            # Atualiza o acumulador e o label de total
            self.total_venda += subtotal_item
            total_texto = f"{self.total_venda:.2f}"
            total_exibicao = total_texto.replace('.', ',')
            self.interface.lbl_total.configure(text=f"TOTAL: R$ {total_exibicao}")

            # Guarda na lista
            self.itens_venda.append({
                "id": id_prod,
                "nome": nome,
                "qtd": self.quantidade_atual,
                "preco": preco_unit,
                "subtotal": subtotal_item
            })

        else:
            messagebox.showwarning("Atenção", f"Código {ean} não localizado!")

        # Reset automático
        self.quantidade_atual = 1.0
        self.interface.lbl_qtd_display.configure(text="1")
        self.interface.entry_barcode.delete(0, 'end')
        self.interface.entry_barcode.focus()

    # (disparar_abertura, finalizar_abertura, etc permanecem iguais...)
    def disparar_abertura(self):
        if not self.caixa_aberto:
            modal = ModalAbertura(master=self, ao_confirmar=self.finalizar_abertura)
            modal.focus_force()
            modal.grab_set()
        else:
            messagebox.showinfo("Aviso", "O caixa já está aberto!")

    def finalizar_abertura(self, valor):
        self.caixa_aberto = True
        self.interface.atualizar_status_caixa(aberto=True)

    def confirmar_fechamento(self):
        if messagebox.askyesno("Sair", "Deseja realmente fechar?"):
            self.destroy()

    def finalizar_venda(self):
        if not self.itens_venda:
            messagebox.showwarning("Atenção", "Não há itens na venda!")
            return

        # Abre o modal de pagamento passando o total e a função de retorno
        ModalPagamento(
            master=self, 
            total_venda=self.total_venda, 
            ao_confirmar=self.concluir_venda_banco
        )

    def concluir_venda_banco(self, id_forma, troco):
        # Pergunta de Segurança (O MessageBox solicitado!)
        if messagebox.askyesno("Confirmar Venda", f"Deseja realmente registrar esta venda?"):
            from utils.pdv_service import salvar_venda_geral
            
            sucesso, resultado = salvar_venda_geral(
                id_operador=UsuarioSessao.id,
                valor_total=self.total_venda,
                lista_itens=self.itens_venda,
                status='CONCLUIDA',
                id_forma_pagamento=id_forma, # <- Enviando a forma capturada
                troco=troco                  # <- Enviando o troco calculado
            )

            if sucesso:
                messagebox.showinfo("Sucesso", f"Venda #{resultado} realizada com sucesso!")
                self.limpar_caixa_pos_venda()
            else:
                messagebox.showerror("Erro", f"Erro crítico ao salvar no banco: {resultado}")
                
    def cancelar_venda_atual(self):
        if not self.itens_venda: return
        
        if messagebox.askyesno("Confirmar", "Deseja cancelar esta venda?"):
            sucesso, resultado = salvar_venda(
                id_operador=UsuarioSessao.id,
                valor_total=self.total_venda,
                lista_itens=None, # Não precisamos gravar itens de venda cancelada
                status='CANCELADA'
            )

            if sucesso:
                messagebox.showwarning("Aviso", f"Venda #{resultado} cancelada e registrada.")
                self.limpar_caixa_pos_venda()

    def limpar_caixa_pos_venda(self):
        # Reseta variáveis lógicas
        self.itens_venda = []
        self.total_venda = 0.0
        self.quantidade_atual = 1.0
        
        # Reseta a Interface
        self.interface.lbl_total.configure(text="TOTAL: R$ 0,00")
        self.interface.lbl_foco_produto.configure(text="Produto Selecionado: NENHUM")
        self.interface.lbl_unit_display.configure(text="R$ 0,00")
        self.interface.lbl_qtd_display.configure(text="1")
        
        # Limpa a tabela visual (remove as linhas)
        for widget in self.interface.table_frame.winfo_children():
            # Não apaga o cabeçalho (que é o primeiro widget)
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