import customtkinter as ctk
from tkinter import ttk
from login_page import LoginPage

class Application:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("IDEA") 
        
        # Configure main window
        self.root.geometry("1024x768")
        
        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width/2) - (1024/2)
        y = (screen_height/2) - (768/2)
        self.root.geometry(f'1024x768+{int(x)}+{int(y)}')

        # Set appearance mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main container
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(side="top", fill="both", expand=True)

        # Show login page
        self.current_page = None
        self.show_login_page()

    def show_login_page(self):
        if self.current_page:
            self.current_page.frame.destroy()
        self.current_page = LoginPage(self.main_container)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = Application()
    app.run()

