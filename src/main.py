from ui.login import LoginWindow
from ui.main_windows import MainWindow
from ui.components.list_prod import ListProd

def open_sistem():
    app_principal = MainWindow()
    app_principal.mainloop()

def main():
    tela_login = LoginWindow(on_login_success=open_sistem)
    tela_login.mainloop()

if __name__ == "__main__":
    main()