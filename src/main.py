""" Importação dos elementos dos arquivos usados para compor o sistema """
from ui.login import LoginWindow
from ui.main_window import MainWindow
from database.connection import Database

""" Instância global do banco de dados para ser compartilhada entre as janelas """
db = Database()

""" Função para executar a janela principal do sistema caso o usuario consiga fazer o login """
def open_sistem():
    app_principal = MainWindow(db_connection=db)
    app_principal.mainloop()

""" Função para executar a tela de login e caso o login seja concluido com sucesso ela executa a janela principal do sistema """
def main():
    tela_login = LoginWindow(on_login_success=open_sistem)
    tela_login.mainloop()

""" Execução do programa em si """
if __name__ == "__main__":
    main()