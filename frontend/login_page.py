import customtkinter as ctk
from tkinter import messagebox
from mandatory_page import MandatoryPage
import requests
from PIL import Image

import os
from config import API_BASE_URL

# Color palette for all pages
colors = {
    "primary": ("#16926B", "#107A59"),     
    "secondary": ("#1A7355", "#0D5940"),    
    "background": ("#F0F7F4", "#0A2E20"),   
    "surface": ("#FFFFFF", "#133326"),     
    "text_primary": ("#0A2E20", "#E6F2ED"), 
    "text_secondary": ("#16926B", "#1A7355"),
    "input_bg": ("#F5FAF7", "#0F291F"),     
    "input_border": ("#16926B", "#1A7355"), 
    "error": "#D32F2F",                     
    "success": "#388E3C"                    
}

class LoginPage:
    def __init__(self, master):
        self.master = master
        
        # Color palette
        self.colors = colors  
        
        # Configure theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        # Main container
        self.frame = ctk.CTkFrame(master, 
                                corner_radius=0,
                                fg_color=self.colors["background"])
        self.frame.pack(fill="both", expand=True)
        
        # Left panel with gradient background
        left_panel = ctk.CTkFrame(self.frame, 
                                fg_color=self.colors["primary"],
                                corner_radius=0)
        left_panel.pack(side="left", fill="both", expand=False)
        left_panel.pack_propagate(False)
        left_panel.configure(width=self.master.winfo_width() * 0.4)

        # Brand text container with enhanced styling
        brand_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        brand_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Semi-transparent overlay
        overlay = ctk.CTkFrame(brand_frame, 
                             fg_color=self.colors["primary"],
                             corner_radius=20,
                             width=300, height=200)
        overlay.place(relx=0.5, rely=0.5, anchor="center")

       
        try:
            image_path = os.path.join(os.path.dirname(__file__), "assets", "branding.png")

            # use CTkImage wrapper
            branding_image = ctk.CTkImage(
                light_image=Image.open(image_path),
                dark_image=Image.open(image_path),
                size=(220, 60)
            )

            # Pass CTkImage (not PhotoImage)
            branding_label = ctk.CTkLabel(left_panel, image=branding_image, text="")
            branding_label.place(relx=0.5, rely=0.95, anchor="s")

        except Exception as e:
            print(f"Error loading branding image: {e}")
        
        
        # Main IDEA text
        ctk.CTkLabel(overlay,
                    text="IDEA",
                    font=ctk.CTkFont(family="Georgia", size=80),
                    text_color=self.colors["text_primary"][1]).place(
                        relx=0.5, rely=0.4, 
                        anchor="center"
                    )

    
        # Right panel
        right_panel = ctk.CTkFrame(self.frame,
                                fg_color=self.colors["surface"])
        right_panel.pack(side="left", fill="both", expand=True)

        # Content container
        content = ctk.CTkFrame(right_panel, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        # Welcome text with enhanced styling
        ctk.CTkLabel(content,
                    text="Welcome Back!",
                    font=ctk.CTkFont(family="Georgia", size=32, weight="bold"),
                    text_color=self.colors["primary"]).pack(pady=(0, 5))

        
        # Input fields with updated styling
        entry_style = {
            "width": 300,
            "height": 50,
            "corner_radius": 10,
            "font": ctk.CTkFont(family="Georgia", size=14),
            "fg_color": self.colors["input_bg"],
            "border_color": self.colors["input_border"],
            "text_color": self.colors["text_primary"]
        }

        # Username entry
        self.username_entry = ctk.CTkEntry(content,
                                         placeholder_text="Username",
                                         **entry_style)
        self.username_entry.pack(pady=10)

        # Password entry
        # self.password_entry = ctk.CTkEntry(content,
        #                                  placeholder_text="Password",
        #                                  show="•",
        #                                  **entry_style)
        # self.password_entry.pack(pady=10)

        # ---------------- Password Field with Icon Inside ----------------
        password_frame = ctk.CTkFrame(content, fg_color="transparent")
        password_frame.pack(pady=10)

        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Password",
            show="•",
            width=300,
            height=50,
            corner_radius=10,
            font=ctk.CTkFont(family="Georgia", size=14),
            fg_color=self.colors["input_bg"],
            border_color=self.colors["input_border"],
            text_color=self.colors["text_primary"]
        )
        self.password_entry.pack()

        self.show_password = False

        def toggle_password(event=None):
            if self.show_password:
                self.password_entry.configure(show="•")
                self.eye_label.configure(text="◉") 
                self.show_password = False
            else:
                self.password_entry.configure(show="")
                self.eye_label.configure(text="◎") 
                self.show_password = True


        # Icon INSIDE the entry
        self.eye_label = ctk.CTkLabel(
            password_frame,
            text="◉",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_secondary"]
        )

        # Place inside (right side, centered vertically)
        self.eye_label.place(relx=0.94, rely=0.5, anchor="center")

        # Click binding
        self.eye_label.bind("<Button-1>", toggle_password)


        # Login button with enhanced styling
        self.login_btn = ctk.CTkButton(content,
                                     text="Sign In",
                                     width=300,
                                     height=50,
                                     corner_radius=10,
                                     font=ctk.CTkFont(family="Georgia", size=16, weight="bold"),
                                     fg_color=self.colors["primary"],
                                     hover_color=self.colors["secondary"],
                                     text_color=self.colors["text_primary"][1],
                                     command=self.login)
        self.login_btn.pack(pady=20)

        # Add window resize handling
        self.master.bind("<Configure>", self._on_resize)


    def _on_resize(self, event):
        """Handle window resize to maintain panel ratios"""
        try:
            if event.width > 200:
                left_width = int(event.width * 0.4)
                right_width = int(event.width * 0.6)
                
                children = self.frame.winfo_children()
                if len(children) >= 2:
                    left_panel = children[0]
                    right_panel = children[1]
                    
                    if left_panel.winfo_exists():
                        left_panel.configure(width=left_width)
                    if right_panel.winfo_exists():
                        right_panel.configure(width=right_width)
        except Exception as e:
            print(f"Resize error: {e}")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        try:
            response = requests.post(f"{API_BASE_URL}/auth/login",
                                     json={"username": username, "password": password},
                                     timeout=5)
            data = response.json()
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect to server.\n{e}")
            return

        if data.get("success"):
            # Success → destroy login frame and go to MandatoryPage
            messagebox.showinfo("Login", "Login successful!")
            self.frame.destroy()
            MandatoryPage(self.master)
        else:
            messagebox.showerror("Error", data.get("message", "Login failed"))
