import customtkinter as ctk
from ui.frente_caixa import TelaPDV
from ui.login import LoginWindow # Certifique-se que o nome do arquivo/classe bate
from utils.auth import UsuarioSessao
import sys

class MainPDV(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Configurações da Janela Principal (PDV)
        self.title("Estimaí - Frente de Caixa")
        self.geometry("1200x800")
        self.after(0, lambda: self.state('zoomed'))
        self.protocol("WM_DELETE_WINDOW", self.confirmar_fechamento)

        # 2. Monta a interface que criamos antes
        self.interface = TelaPDV(master=self)
        self.interface.pack(fill="both", expand=True)

        # 3. Personaliza com os dados do operador que logou
        self.interface.lbl_operador.configure(text=f"OPERADOR: {UsuarioSessao.nome}")
        
        # 4. Inicia com o caixa travado
        self.interface.atualizar_status_caixa(aberto=False)

    def confirmar_fechamento(self):
        from tkinter import messagebox
        if messagebox.askyesno("Sair", "Deseja realmente fechar o sistema de caixa?"):
            self.destroy()

# --- FUNÇÃO DE ARRANQUE (Onde a mágica acontece) ---
def iniciar_sistema():
    # 1. Primeiro, criamos e rodamos apenas a janela de Login
    # Passamos 'montar_pdv' como a função que deve ser chamada no sucesso
    def montar_pdv():
        app_pdv = MainPDV()
        app_pdv.mainloop()

    # Inicia a sua classe LoginWindow
    login = LoginWindow(on_login_success=montar_pdv)
    login.mainloop()

if __name__ == "__main__":
    iniciar_sistema()