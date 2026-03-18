import customtkinter as ctk
from tkinter import messagebox, filedialog
import requests
from config import API_BASE_URL

class ExportPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.label = ctk.CTkLabel(self, text="Export Data to CSV")
        self.label.pack(pady=10)

        self.export_button = ctk.CTkButton(self, text="Choose Folder & Export", command=self.export_data)
        self.export_button.pack(pady=20)

    def export_data(self):
        folder_path = filedialog.askdirectory(title="Select Download Folder")
        if not folder_path:
            messagebox.showwarning("Cancelled", "No folder selected")
            return

        try:
            res = requests.post(f"{API_BASE_URL}/export/", json={"download_path": folder_path})
            result = res.json()

            if result.get("success"):
                messagebox.showinfo("Exported", result.get("message"))
            else:
                messagebox.showerror("Error", result.get("message"))
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")
