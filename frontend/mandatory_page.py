
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
from tkcalendar import Calendar
from optional_page import OptionalPage
import os
from config import API_BASE_URL
import requests
import tkinter.ttk as ttk
from datetime import datetime, date, time, timezone
from PIL import Image,ImageTk

class ToolTip:
    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.delay = delay
        self._after_id = None

        widget.bind("<Enter>", self.schedule_show)
        widget.bind("<Leave>", self.hide_tooltip)

    def schedule_show(self, _event):
        self._after_id = self.widget.after(self.delay, self.show_tooltip)

    def show_tooltip(self):
        if self.tip_window or not self.text:
            return
        try:
            x, y, _, _ = self.widget.bbox("insert") if self.widget.bbox("insert") else (0, 0, 0, 0)
        except Exception:
            x, y = 0, 0
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(
            tw,
            text=self.text,
            fg_color="#FFFFFF",
            text_color="#0A2E20",
            corner_radius=10,
            font=ctk.CTkFont(size=13, family="Georgia"),
            padx=10,
            pady=5
        )
        label.pack()

    def hide_tooltip(self, _event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

colors = {
    "primary": ("#16926B", "#107A59"),
    "secondary": ("#1A7355", "#0D5940"),
    "background": ("#F0F7F4", "#0A2E20"),
    "surface": ("#FFFFFF", "#133326"),
    "text_primary": ("#0A2E20", "#E6F2ED"),
    "input_bg": ("#F5FAF7", "#0F291F"),
    "input_border": ("#16926B", "#1A7355"),
}

class MandatoryPage:
    def __init__(self, master, form_data=None, optional_data=None):
        self.master = master
        self.optional_data = optional_data or {}

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.frame = ctk.CTkFrame(master, corner_radius=0, fg_color=colors["background"])
        self.frame.pack(fill="both", expand=True)

        # Left panel
        left_panel = ctk.CTkFrame(self.frame, fg_color=colors["primary"][0], corner_radius=0)
        left_panel.pack(side="left", fill="both", expand=False)
        left_panel.pack_propagate(False)
        left_panel.configure(width=self.master.winfo_width() * 0.4)

        brand_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        brand_frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(
            brand_frame,
            text="Mandatory Fields",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color=colors["surface"][0]
        ).pack()
        # Branding image at bottom
        try:
            image_path = os.path.join(os.path.dirname(__file__), "assets", "branding.png")
            branding_image = ctk.CTkImage(
                light_image=Image.open(image_path),
                dark_image=Image.open(image_path),
                size=(220, 60)
            )
            branding_label = ctk.CTkLabel(left_panel, image=branding_image, text="")
            branding_label.place(relx=0.5, rely=0.95, anchor="s")  # position bottom center
        except Exception as e:
            print(f"Branding image load error: {e}")


        # Right panel
        right_panel = ctk.CTkFrame(self.frame, fg_color="white")
        right_panel.pack(side="left", fill="both", expand=True)
        right_panel.configure(width=self.master.winfo_width() * 0.6)

        content = ctk.CTkFrame(right_panel, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        form_frame = ctk.CTkFrame(content, fg_color="transparent")
        form_frame.pack(padx=40, pady=20)

        entry_style = {
            "width": 300,
            "height": 45,
            "corner_radius": 8,
            "font": ctk.CTkFont(family="Georgia", size=14),
            "fg_color": colors["input_bg"][0],
            "border_color": "#A0A0A0",   
            "text_color": "#000000",     
        }


        self.entries = {}

        # Start datetime
        self.create_field_with_calendar(
            form_frame, "start_datetime", "Start Date & Time", entry_style,
            placeholder="(YYYY-MM-DD HH:MM:SS)"
        )
        ToolTip(self.entries["start_datetime"], "Enter the start date and time (UTC). Future dates not allowed.")

        # End datetime
        self.create_field_with_calendar(
            form_frame, "end_datetime", "End Date & Time", entry_style,
            placeholder="(YYYY-MM-DD HH:MM:SS)"
        )
        ToolTip(self.entries["end_datetime"], "Enter the end date and time (UTC). Must be after start time.")

        # Domain + API Key
        self.create_field(form_frame, "domain", "Domain", entry_style)
        self.create_field(form_frame, "api_key", "API Key", entry_style, show="•")

        # CSV Download path
        path_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        path_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            path_frame,
            text="Download Path",
            font=ctk.CTkFont(size=17, family="Georgia"),
            text_color="#000000",
            width=160, anchor="w"
        ).pack(side="left")

        csv_entry_style = entry_style.copy()
        csv_entry_style["width"] = 180
        self.entries["csv_download_path"] = ctk.CTkEntry(path_frame, **csv_entry_style)
        self.entries["csv_download_path"].pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            path_frame,
            text="Browse",
            width=110,
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color=colors["primary"][0],
            hover_color=colors["secondary"][0],
            text_color=colors["surface"][0],
            command=self.browse_file
        ).pack(side="left", padx=(10, 0))

        # Next button
        self.next_btn = ctk.CTkButton(
            form_frame,
            text="Next →",
            width=300,
            height=50,
            corner_radius=10,
            font=ctk.CTkFont(family="Georgia", size=16, weight="bold"),
            fg_color=colors["primary"][0],
            hover_color=colors["secondary"][0],
            text_color=colors["surface"][0],
            command=self.go_next,
            state="disabled"
        )
        self.next_btn.pack(pady=(30, 20))

        for entry in self.entries.values():
            entry.bind("<KeyRelease>", lambda e: self.check_fields())

        if form_data:
            self.fill_data(form_data)
            self.check_fields()

        self.master.bind("<Configure>", self._on_resize)

    def create_field(self, parent, field_id, label_text, style_dict, show=None, placeholder=None):
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            field_frame,
            text=label_text,
            font=ctk.CTkFont(size=17, family="Georgia"),
            text_color="#000000",
            width=160,
            anchor="w"
        ).pack(side="left")

        entry = ctk.CTkEntry(field_frame, show=show, placeholder_text=placeholder, **style_dict)
        entry.pack(side="left", padx=(10, 0))
        self.entries[field_id] = entry

    def create_field_with_calendar(self, parent, field_id, label_text, style_dict, placeholder=None):
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            field_frame,
            text=label_text,
            font=ctk.CTkFont(size=17, family="Georgia"),
            text_color="#000000",
            width=160,
            anchor="w"
        ).pack(side="left")

        entry = ctk.CTkEntry(field_frame, placeholder_text=placeholder, **style_dict)
        entry.pack(side="left", padx=(10, 0))
        self.entries[field_id] = entry

        cal_btn = ctk.CTkButton(
            field_frame,
            text="📅",
            width=45,
            command=lambda e=entry: self.open_calendar(e)
        )
        cal_btn.pack(side="left", padx=(10, 0))

    def open_calendar(self, entry):
        top = Toplevel(self.master)
        top.title("Select Date & Time")
        top.transient(self.master)
        
        top.focus_force()

        
        top.configure(bg="white")

        style = ttk.Style(top)
        style.theme_use("default")
        style.configure("TCalendar", background="white", foreground="black", bordercolor="#16926B")
        style.map("TCalendar", background=[("selected", "#16926B")], foreground=[("selected", "white")])

        cal = Calendar(
            top,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            showweeknumbers=False,
            background="white",
            foreground="black",
            headersbackground="#e6f2ed",
            headersforeground="#0A2E20",
            selectbackground="#16926B",
            selectforeground="white",
            bordercolor="#16926B",
            # maxdate=date.today() # Prevent future dates
        )
        cal.pack(pady=10)

        time_frame = ctk.CTkFrame(top, fg_color="transparent")
        time_frame.pack(pady=10)

        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(60)]
        seconds = [f"{s:02d}" for s in range(60)]

        hour_cb = ctk.CTkComboBox(time_frame, values=hours, width=60)
        hour_cb.set("00")
        hour_cb.pack(side="left", padx=5)

        minute_cb = ctk.CTkComboBox(time_frame, values=minutes, width=60)
        minute_cb.set("00")
        minute_cb.pack(side="left", padx=5)

        second_cb = ctk.CTkComboBox(time_frame, values=seconds, width=60)
        second_cb.set("00")
        second_cb.pack(side="left", padx=5)

        def set_date():
            selected_date = datetime.strptime(cal.get_date(), "%Y-%m-%d").date()
            selected_time = time(int(hour_cb.get()), int(minute_cb.get()), int(second_cb.get()))
            selected_dt = datetime.combine(selected_date, selected_time)

            # Compare UTC times properly
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)  # Remove tzinfo for comparison
            if selected_dt > now_utc:
                messagebox.showerror("Invalid Selection", "Future date or time cannot be selected.")
                return

            entry.delete(0, ctk.END)
            entry.insert(0, selected_dt.strftime("%Y-%m-%d %H:%M:%S"))
            self.check_fields()
            top.destroy()

        ctk.CTkButton(top, text="Select", command=set_date).pack(pady=10)

    def browse_file(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entries["csv_download_path"].delete(0, ctk.END)
            self.entries["csv_download_path"].insert(0, folder)
            self.check_fields()

    def fill_data(self, form_data):
        for key, value in form_data.items():
            if key in self.entries and value:
                self.entries[key].delete(0, ctk.END)
                self.entries[key].insert(0, value)
        # Force redraw immediately after restoring data
        self.refresh()

    def refresh(self):
        """Force refresh of all visible widgets to avoid hover lag."""
        self.frame.update_idletasks()
        self.frame.update()

    def check_fields(self):
        required_fields = ["start_datetime", "end_datetime", "domain", "api_key", "csv_download_path"]
        all_filled = all(self.entries[f].get().strip() for f in required_fields)
        self.next_btn.configure(state="normal" if all_filled else "disabled")

    def go_next(self):
        form_data = {k: self.entries[k].get().strip() for k in self.entries}
        if not os.path.isdir(form_data["csv_download_path"]):
            messagebox.showerror("Error", "CSV Download Path must be a valid folder.")
            return

        try:
            start_dt = datetime.strptime(form_data["start_datetime"], "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(form_data["end_datetime"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            messagebox.showerror("Error", "Dates must be in format YYYY-MM-DD HH:MM:SS")
            return

        if start_dt > end_dt:
            messagebox.showerror("Error", "Start Date cannot be later than End Date.")
            return

        # Make datetimes UTC-aware before converting to timestamp
        start_dt_utc = start_dt.replace(tzinfo=timezone.utc)
        end_dt_utc = end_dt.replace(tzinfo=timezone.utc)
        
        form_data["start_timestamp_ms"] = int(start_dt_utc.timestamp() * 1000)
        form_data["end_timestamp_ms"] = int(end_dt_utc.timestamp() * 1000)

        try:
            response = requests.post(f"{API_BASE_URL}/mandatory/", json=form_data)
            if response.status_code != 200:
                messagebox.showerror("Error", f"Failed to store data: {response.json().get('message', 'Unknown error')}")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to backend: {e}")
            return

        self.frame.destroy()
        OptionalPage(self.master, form_data=form_data, optional_data=self.optional_data)

    def _on_resize(self, event):
        try:
            if event.width > 200:
                children = self.frame.winfo_children()
                if len(children) >= 2:
                    children[0].configure(width=int(event.width * 0.4))
                    children[1].configure(width=int(event.width * 0.6))
        except Exception as e:
            print(f"Resize error: {e}")
