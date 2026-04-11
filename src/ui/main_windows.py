import customtkinter as ctk
from ui.components.list_prod import ListProd

class MainWindow(ctk.CTk):
    def __init__(self, db_connection=None):
        super().__init__()
        self.db = db_connection
        self.after(0, lambda: self.state('zoomed'))
        self.title("SGE Manager")

        self.grid_columnconfigure(0, minsize=250)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=350, corner_radius=5)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="💧 SGE Manager", font=("Arial", 22, "bold")).pack(pady=30)

        self.btn_prod = ctk.CTkButton(self.sidebar, text="📦 Produtos", command=self.mostrar_produtos)
        self.btn_prod.pack(pady=10, padx=20, fill="x")

        
        self.btn_prod = ctk.CTkButton(self.sidebar, text="📦 Produtos", command=self.mostrar_produtos)
        self.btn_prod.pack(pady=10, padx=20, fill="x")

        self.area_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.area_principal.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.mostrar_produtos()

    def mostrar_produtos(self):
        for widget in self.area_principal.winfo_children():
            widget.destroy()
            
        self.tela = ListProd(master=self.area_principal, db_connection=self.db)
        self.tela.pack(fill="both", expand=True)

# if __name__ == "__main__":
#     app = MainWindow()
#     app.mainloop()