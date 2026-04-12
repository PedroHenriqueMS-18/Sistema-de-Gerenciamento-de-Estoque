import customtkinter as ctk
from tkinter import messagebox

"""Classe responsável por gerar e gerenciar a interface gráfica da janela de login."""
class LoginWindow(ctk.CTk):
    """Inicializa a janela, define configurações de tema, estado e vincula eventos de teclado."""
    def __init__(self, on_login_success):
        super().__init__()

        self.on_login_success = on_login_success

        self.after(0, lambda: self.state('zoomed'))

        self.title("SGE - Login")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.setup_ui()
        self.bind("<Return>", lambda event: self.login_check())
        self.entry_user.focus_set()

    """Cria e posiciona todos os elementos visuais (widgets) dentro do frame de login."""
    def setup_ui(self):
        self.login_frame = ctk.CTkFrame(self, width=400, height=500, corner_radius=20)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.label_logo = ctk.CTkLabel(self.login_frame, text="SGE Manager", font=ctk.CTkFont(family="Arial", size=28, weight="bold"))
        self.label_logo.place(relx=0.5, rely=0.15, anchor="center")

        self.label_sub = ctk.CTkLabel(self.login_frame, text="Faça login para continuar", font=("Arial", 12))
        self.label_sub.place(relx=0.5, rely=0.25, anchor="center")

        self.entry_user = ctk.CTkEntry(self.login_frame, placeholder_text="Usuário", width=300, height=45)
        self.entry_user.place(relx=0.5, rely=0.45, anchor="center")

        self.entry_pass = ctk.CTkEntry(self.login_frame, placeholder_text="Senha", show="*", width=300, height=45)
        self.entry_pass.place(relx=0.5, rely=0.6, anchor="center")

        self.btn_login = ctk.CTkButton(
            self.login_frame,
            text="ENTRAR NO SISTEMA",
            fg_color="#27cc71",
            hover_color="#27ae60",
            font=("Arial", 14, "bold"),
            width=300,
            height=45,
            command=self.login_check
        )
        self.btn_login.place(relx=0.5, rely=0.8, anchor="center")
        
    """Coleta os dados dos campos e valida as credenciais para autorizar o acesso ao sistema."""
    def login_check(self):
        user = self.entry_user.get()
        password = self.entry_pass.get()

        if user == "admin" and password == "123":
            self.destroy()
            self.on_login_success()
        else:
            messagebox.showerror("Erro de Acesso", "Usuário ou senha incorretos!")