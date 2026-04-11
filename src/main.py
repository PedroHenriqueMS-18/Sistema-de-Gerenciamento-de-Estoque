from ui.login import LoginWindow
from ui.main_windows import MainWindow

def main():
    app = LoginWindow(on_login_success=MainWindow)
    app.mainloop()

if __name__ == "__main__":
    main()