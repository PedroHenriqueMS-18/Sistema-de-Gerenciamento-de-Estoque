import customtkinter as ctk
from ui.frente_caixa import TelaPDV
from ui.login import LoginWindow 
from utils.auth import UsuarioSessao
from ui.components.modal_abertura import ModalAbertura
from tkinter import messagebox
import sys

class MainPDV(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Configurações da Janela Principal
        self.title("Estimaí - Frente de Caixa")
        self.geometry("1200x800")
        self.after(0, lambda: self.state('zoomed'))
        self.protocol("WM_DELETE_WINDOW", self.confirmar_fechamento)

        # 2. Estado do Sistema e Variáveis de Venda
        self.caixa_aberto = False
        self.quantidade_atual = 1.0  # Quantidade padrão inicial
        self.total_venda = 0.0

        # 3. Monta a interface
        self.interface = TelaPDV(master=self)
        self.interface.pack(fill="both", expand=True)

        # 4. Personaliza com os dados do operador
        self.interface.lbl_operador.configure(text=f"OPERADOR: {UsuarioSessao.nome}")
        
        # 5. Inicia travado
        self.interface.atualizar_status_caixa(aberto=False)

        # 6. Mapeamento de Teclas e Eventos
        self.configurar_binds()

        # Gatilho automático para abertura após 0.5s
        self.after(500, self.disparar_abertura)

    def configurar_binds(self):
        """Configura todos os atalhos de teclado"""
        # Atalho para abertura (F2 ou 'a' como você preferir)
        self.bind("<F2>", lambda e: self.disparar_abertura)
        
        # Escutador do Asterisco (*) no campo de código de barras
        self.interface.entry_barcode.bind("<KeyRelease>", self.detectar_multiplicador)
        
        # Enter para processar o item
        self.interface.entry_barcode.bind("<Return>", self.processar_item)

    def detectar_multiplicador(self, event):
        """Verifica se o operador digitou um multiplicador (ex: 3*)"""
        texto = self.interface.entry_barcode.get()
        
        if "*" in texto:
            try:
                # Separa o número antes do *
                qtd_str = texto.split("*")[0].replace(',', '.')
                
                # Se digitou apenas * sem número, assume 1, se não, converte
                qtd_val = float(qtd_str) if qtd_str else 1.0
                
                if qtd_val > 0:
                    self.quantidade_atual = qtd_val
                    # Atualiza o display azul na interface
                    self.interface.lbl_qtd_display.configure(text=f"{int(qtd_val) if qtd_val.is_integer() else qtd_val}")
                
                # Limpa o campo para receber o código de barras
                self.interface.entry_barcode.delete(0, 'end')
                
            except ValueError:
                # Se não for número válido, reseta
                self.interface.entry_barcode.delete(0, 'end')
                self.quantidade_atual = 1.0
                self.interface.lbl_qtd_display.configure(text="1")

    def processar_item(self, event=None):
        """Função que será chamada ao dar Enter no código de barras"""
        if not self.caixa_aberto:
            return

        ean = self.interface.entry_barcode.get().strip()
        if not ean:
            return

        print(f"Buscando produto: {ean} | Quantidade: {self.quantidade_atual}")
        
        # --- AQUI ENTRARÁ SUA BUSCA NO BANCO ---
        # Exemplo: produto = buscar_produto(ean)
        # if produto: 
        #    self.adicionar_item_tabela(produto)
        
        # Após processar, reseta a quantidade para o próximo item
        self.quantidade_atual = 1.0
        self.interface.lbl_qtd_display.configure(text="1")
        self.interface.entry_barcode.delete(0, 'end')

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
        print(f"Caixa aberto com R$ {valor:.2f}")

    def confirmar_fechamento(self):
        if messagebox.askyesno("Sair", "Deseja realmente fechar o sistema de caixa?"):
            self.destroy()

def iniciar_sistema():
    def montar_pdv():
        app_pdv = MainPDV()
        app_pdv.mainloop()

    login = LoginWindow(on_login_success=montar_pdv)
    login.mainloop()

if __name__ == "__main__":
    iniciar_sistema()