import customtkinter as ctk
from ui.frente_caixa import TelaPDV
from ui.login import LoginWindow 
from utils.auth import UsuarioSessao
from ui.components.modal_abertura import ModalAbertura
from tkinter import messagebox
from utils.pdv_service import buscar_produto_por_ean
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

        self.interface.lbl_operador.configure(text=f"OPERADOR: {UsuarioSessao.nome}")
        self.interface.atualizar_status_caixa(aberto=False)

        self.configurar_binds()
        self.after(500, self.disparar_abertura)

    def configurar_binds(self):
        # CORREÇÃO 2: Faltavam os parênteses () no disparar_abertura e binds duplicados removidos
        self.bind("<F2>", lambda e: self.disparar_abertura())
        self.interface.entry_barcode.bind("<Return>", self.processar_item)
        self.interface.btn_buscar.configure(command=self.processar_item)
        self.interface.entry_barcode.bind("<KeyRelease>", self.detectar_multiplicador)

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

def iniciar_sistema():
    def montar_pdv():
        app_pdv = MainPDV()
        app_pdv.mainloop()
    login = LoginWindow(on_login_success=montar_pdv)
    login.mainloop()

if __name__ == "__main__":
    iniciar_sistema()