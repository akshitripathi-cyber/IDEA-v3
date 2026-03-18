from cProfile import label

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import re
import requests
from config import API_BASE_URL
import json
from PIL import Image
import os
from tkinter import filedialog
import time
import threading
import shutil
import tempfile
import csv as _csv 
from numbers import Number
import copy
from preferences_manager import save_preferences, load_preferences, delete_preference
from tkinter import simpledialog


colors = {
    "primary": ("#16926B", "#107A59"),
    "secondary": ("#1A7355", "#0D5940"),
    "background": ("#F0F7F4", "#0A2E20"),
    "surface": ("#FFFFFF", "#133326")
}



INCLUDES_OPTIONS = ["meta", "feedback", "custom_fields", "private_notes", "queue", "smart_intents"]

class OptionalPage:


    def __init__(self, master, form_data=None, optional_data=None):
        self.master = master
        self.form_data = form_data or {}
        self.optional_data = optional_data or {}
        self.is_exporting = False
        # self._sanitize_optional_data()

        # Appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        # Main frame
        self.frame = ctk.CTkFrame(master, corner_radius=0, fg_color=colors["background"])
        self.frame.pack(fill="both", expand=True)

        # left panel
        left_panel = ctk.CTkFrame(self.frame, fg_color=colors["primary"], corner_radius=0)
        left_panel.pack(side="left", fill="both", expand=False)

        # Safe width detection
        try:
            self.master.update_idletasks()
            master_width = max(300, int(self.master.winfo_width()))
        except Exception:
            master_width = 900
        left_panel.configure(width=int(master_width * 0.35))

        brand_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        brand_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            brand_frame,
            text="Optional Filters",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color=colors["surface"]
        ).pack()

        # helpshift image
        try:
            image_path = os.path.join(os.path.dirname(__file__), "assets", "branding.png")
            if os.path.exists(image_path):
                branding_image = ctk.CTkImage(
                    light_image=Image.open(image_path),
                    dark_image=Image.open(image_path),
                    size=(220, 60)
                )
                branding_label = ctk.CTkLabel(left_panel, image=branding_image, text="")
                branding_label.place(relx=0.5, rely=0.95, anchor="s")
        except Exception as e:
            print("Branding load error:", e)

        # right panel
        right_panel = ctk.CTkFrame(self.frame, fg_color=colors["surface"])
        right_panel.pack(side="left", fill="both", expand=True)
        right_panel.configure(width=int(master_width * 0.65))

        


       # ================= TOP BAR =================
        top_bar = ctk.CTkFrame(right_panel, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(15,5))

        top_left = ctk.CTkFrame(top_bar, fg_color="transparent")
        top_left.pack(side="left")

        top_right = ctk.CTkFrame(top_bar, fg_color="transparent")
        top_right.pack(side="right")

        import webbrowser

        glossary_link = ctk.CTkLabel(
            top_left,
            text="View Glossary for IDEA",
            text_color="#1E90FF",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            cursor="hand2"
        )
        glossary_link.pack(side="left", padx=(0,15))

        glossary_link.bind("<Button-1>", lambda e: webbrowser.open_new(
            "https://helpshift.atlassian.net/wiki/spaces/SUP/pages/5604147897/Glossary+for+IDEA"
        ))

        self.saved_filters_btn = ctk.CTkButton(
            top_right,
            text="☰",
            width=40,
            height=36,
            corner_radius=10,
            fg_color=colors["primary"],
            hover_color=colors["secondary"],
            text_color=colors["surface"],
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            command=self.toggle_saved_filters
        )
        self.saved_filters_btn.pack(side="left")

        # Dropdown
        self.saved_filters_frame = ctk.CTkFrame(
            right_panel,
            width=350,
            height=200,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color="#E5E7EB"
        )
        self.saved_filters_frame.place_forget()

        # ================= BODY (FIXED) =================
        body_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        body_frame.pack(fill="both", expand=True)

        # 🔥 CREATE CONTENT FIRST (IMPORTANT)
        self.content = ctk.CTkScrollableFrame(body_frame, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        # 🔥 NOW SAFE TO ADD CARDS
        self.entries = {}
        print("Restoring optional data:", self.optional_data)

        self.fields = [
            ("includes", "Include extra response data."),
            ("metadata_columns","Enter the field names which you want in separte columns."),
            ("tags", "Filter by tags."),
            ("languages", "Filter by languages."),
            ("app-ids", "Select app IDs."),
            ("end-user-ids", "Enter End User IDs"),
            ("custom_fields", "Filter by custom fields."),
            ("ids[issue]", "Enter issue IDs."),
            ("state", "Select issue states."),
            ("platform-types", "Select platform types."),
            ("feedback-rating", "Filter by feedback rating."),
            ("assignee_emails", "Filter by assignee emails."),
            ("author_emails", "Filter by author emails."),
            ("queue_ids", "Select queue IDs."),
            ("sort-by", "Sort by field."),
            ("sort-order", "Set sort order."),
            ("state_since", "Unix timestamp (ms) since which issues of a state are retrieved"),
            ("updated_until", "Unix timestamp (ms) until issues were updated"),
            ("updated_since", "Unix timestamp (ms) since issues were updated"),
            ("state-until", "Unix timestamp (ms) until issues of a state are retrieved"),
            ("page", "Page number (pagination)"),
            ("page-size", "Results per page (1–1000)"),
            ("issue_modes", "Issue modes (comma separated)"),
            ("excludes", "Exclude fields (comma separated)"),
            ("redacted", "true / false"),
            ("timestamp-format", "unix or iso-8601"),
            ("notes", "Notes must contain ALL words (comma separated)"),
            ("feedback-comment", "Feedback must contain ALL words (comma separated)")
        ]

        for field, desc in self.fields:
            try:
                self.add_card(field, desc)
            except Exception as e:
                print(f"Error adding card for {field}: {e}")

        # 🔥 FIX BROKEN DATA BEFORE UI BUILDS
        cf = self.optional_data.get("custom_fields")

        if not isinstance(cf, dict):
            self.optional_data["custom_fields"] = self._fix_custom_fields(
                self.optional_data.get("custom_fields")
            )

        # ================= BUTTONS =================
        self.btn_frame = ctk.CTkFrame(body_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=20, pady=(10, 10))


        self.back_btn = ctk.CTkButton(
            self.btn_frame,
            text="← Previous",
            width=140,
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color=colors["primary"],
            hover_color=colors["secondary"],
            text_color=colors["surface"],
            command=self.go_previous
        )
        self.back_btn.pack(side="left", padx=(0, 20))   


        self.clear_btn = ctk.CTkButton(
            self.btn_frame,
            text="Clear Filters",
            width=140,
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color=colors["primary"],
            hover_color=colors["secondary"],
            text_color="white",
            command=self.clear_all_filters
        )
        self.clear_btn.pack(side="right", padx=(0, 20))



        self.save_btn = ctk.CTkButton(
            self.btn_frame,
            text="Save Filters",
            width=140,
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color=colors["primary"],
            hover_color=colors["secondary"],
            text_color=colors["surface"],
            command=self.save_current_filters
        )

        self.save_btn.pack(side="right", padx=(0,20))

        self.submit_btn = ctk.CTkButton(
            self.btn_frame,
            text="Export",
            width=140,
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            fg_color=colors["primary"],
            hover_color=colors["secondary"],
            text_color=colors["surface"],
            command=self.submit
        )
        self.submit_btn.pack(side="right", padx=(20, 17))  
        self.master.bind("<Button-1>", self._close_dropdown_on_click)

        # downloading animation frame
        self._progress_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        self._progress_frame.pack(fill="x", pady=(0, 10))
        self._progress_frame.pack_forget()  # hidden until export starts

        self._progress_label = ctk.CTkLabel(
            self._progress_frame,
            text="",
            anchor="w",
            font=ctk.CTkFont(family="Georgia", size=16)
        )
        self._progress_label.pack(fill="x", padx=20, pady=(6, 6))

        # marquee components
        # Track (light background)
        self._marquee_track = ctk.CTkFrame(
            self._progress_frame,
            fg_color="#e8edf2",
            height=14,
            corner_radius=8
        )
        self._marquee_track.pack(fill="x", padx=20, pady=(0, 10))

        # Moving bar (colored)
        self._marquee_bar = ctk.CTkFrame(
            self._marquee_track,
            fg_color=colors["primary"],
            width=80,
            height=14,
            corner_radius=8
        )

        self._marquee_bar.place(x=-120, y=0)

    def _sanitize_optional_data(self):
        
        cleaned = {}

        for k, v in (self.optional_data or {}).items():
            if v is None:
                continue

            # Widget-dict with _get_json()
            if isinstance(v, dict):
                try:
                    get_json_fn = v.get("_get_json")
                    if callable(get_json_fn):
                        ok, out = get_json_fn()
                        if ok:
                            cleaned[k] = out
                            continue
                except Exception:
                    pass

            # List/tuple values
            if isinstance(v, (list, tuple)):
                out_list = []

                for item in v:
                    try:
                        if hasattr(item, "get") and callable(getattr(item, "get")):
                            value = item.get()
                            if value is not None:
                                item = value
                    except Exception:
                        pass

                    if item is None:
                        continue
                    if isinstance(item, str) and item == "":
                        continue

                    s = str(item)
                    if (
                        s.endswith("_var") or
                        s in (
                            "btn_var", "option_var", "exists_var",
                            "no_filter_var", "operator_var",
                            "condition_var", "value_var"
                        )
                    ):
                        continue

                    if isinstance(item, (str, int, float, bool)):
                        out_list.append(item)
                    else:
                        out_list.append(s)

                cleaned[k] = out_list
                continue

            # String values
            if isinstance(v, str):
                if v.endswith("_var") or v in ("btn_var",):
                    cleaned[k] = None
                else:
                    cleaned[k] = v
                continue

            # Numbers / booleans
            if isinstance(v, bool) or isinstance(v, Number):
                cleaned[k] = v
                continue

            # Fallback
            cleaned[k] = v

        self.optional_data = cleaned

    def normalize_optional_data(self, raw_data: dict) -> dict:
        """
        Converts widget data into a stable persistence format.
        """
        normalized = {}

        for field, widget in self.entries.items():
            ok, value = widget["_get_json"]()

            if ok:
                normalized[field] = value

        return normalized

    def restore_optional_data(self, saved_data: dict):
        """
        Restores saved data into self.optional_data safely.
        """
        if not isinstance(saved_data, dict):
            self.optional_data = {}
        else:
            self.optional_data = saved_data.copy()

    def add_card(self, field, description):
        card = ctk.CTkFrame(self.content, fg_color=colors["background"], corner_radius=12)
        card.pack(fill="x", pady=8, padx=10)

        header = ctk.CTkFrame(card, fg_color=colors["primary"], corner_radius=12)
        header.pack(fill="x")
        header_label = ctk.CTkLabel(
            header, text=field, font=ctk.CTkFont(family="Georgia", size=16, weight="bold"),
            text_color=colors["surface"], anchor="w", padx=10
        )
        header_label.pack(fill="x", pady=6)

        body = ctk.CTkFrame(card, fg_color=colors["surface"], corner_radius=12)
        body.pack(fill="x", pady=(0,6))
        body.pack_forget()
        

        # Description
        ctk.CTkLabel(
            body, text=description, font=ctk.CTkFont(family="Georgia", size=13),
            text_color=colors["primary"], wraplength=480, justify="left"
        ).pack(pady=(10,6), padx=10, anchor="w")

        def refocus():
            input_entry.after(50, lambda: (
                input_entry.focus_set(),
                input_entry.selection_range(0, "end")
            ))

        if field == "sort-by":
        
            saved_value = self.optional_data.get(field, "state-change-time")

            widget = ctk.CTkOptionMenu(
                body,
                values=["creation-time", "state-change-time"],
                width=250,
                corner_radius=8,
                font=ctk.CTkFont(family="Georgia", size=14),
                fg_color=colors["primary"],
                button_color=colors["primary"],
                button_hover_color=colors["secondary"],
                text_color=colors["surface"]
            )

            widget.set(saved_value)
            widget.pack(padx=10, pady=10, anchor="w")

            def _get_json():
                val = widget.get()
                if not val:
                    return False, None
                return True, val

            self.entries[field] = {
                "widget": widget,
                "_get_json": _get_json
            }


        elif field == "sort-order":
        
            saved_value = self.optional_data.get(field, "desc")
        
            widget = ctk.CTkOptionMenu(
                body,
                values=["asc", "desc"],
                width=250,
                corner_radius=8,
                font=ctk.CTkFont(family="Georgia", size=14),
                fg_color=colors["primary"],
                button_color=colors["primary"],
                button_hover_color=colors["secondary"],
                text_color=colors["surface"]
            )
        
            widget.set(saved_value)
            widget.pack(padx=10, pady=10, anchor="w")
        
            def _get_json():
                val = widget.get()
                if not val:
                    return False, None
                return True, val
        
            self.entries[field] = {
                "widget": widget,
                "_get_json": _get_json
            }
        
        elif field == "notes":
        
            container = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=12)
            container.pack(fill="x", padx=10, pady=(0, 10))

            raw_data = self.optional_data.get(field)
            if not isinstance(raw_data, dict):
                current_data = {"and": [], "or": [], "nor": []}
            else:
                current_data = {"and": [], "or": [], "nor": []}
                for k in ("and", "or", "nor"):
                    items = raw_data.get(k, [])
                    for it in items:
                        if isinstance(it, str):
                            current_data[k].append(it)

            input_frame = ctk.CTkFrame(container, fg_color="transparent")
            input_frame.pack(fill="x", padx=10, pady=(8, 6))

            input_var = tk.StringVar()
            input_entry = ctk.CTkEntry(
                input_frame, placeholder_text="Enter note keyword",
                textvariable=input_var, width=220, height=32, corner_radius=8,
                font=("Georgia", 12)
            )
            input_entry.pack(side="left", padx=(0, 6))

            option_var = tk.StringVar(value="and")
            option_menu = ctk.CTkOptionMenu(
                input_frame, variable=option_var, values=["and", "or", "nor"],
                width=90, height=32, corner_radius=8,
                fg_color=colors["primary"], button_color=colors["primary"],
                button_hover_color=colors["secondary"], text_color=colors["surface"],
                font=("Georgia", 12)
            )
            option_menu.pack(side="left", padx=(0, 6))

            def add_item():
                text = input_var.get().strip()
                if not text:
                    return
                cat = option_var.get()
                if text not in current_data.get(cat, []):
                    current_data.setdefault(cat, []).append(text)
                input_var.set("")
                refresh_list()

            add_btn = ctk.CTkButton(
                input_frame, text="Add", width=70, height=32,
                fg_color=colors["primary"], hover_color=colors["secondary"],
                text_color=colors["surface"], font=("Georgia", 12),
                command=add_item
            )
            add_btn.pack(side="left", padx=(4, 0))

            # list section
            list_frame = ctk.CTkFrame(container, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=12, pady=(6, 4))

            def refresh_list():
                for child in list_frame.winfo_children():
                    child.destroy()
                has_any = False
                for k, v_list in current_data.items():
                    for val in list(v_list):
                        has_any = True
                        row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                        row.pack(fill="x", padx=6, pady=3)

                        inner = ctk.CTkFrame(row, fg_color="transparent")
                        inner.pack(fill="x", padx=10, pady=4)

                        text_display = f"{k.upper()} → {val}"
                        label = ctk.CTkLabel(
                            inner, text=text_display, anchor="w", justify="left",
                            text_color=colors["primary"], font=("Georgia", 12), wraplength=330
                        )
                        label.pack(side="left", fill="x", expand=True, padx=(0, 6))

                        def make_edit(cat, value):
                            def _edit():
                                input_var.set(value)
                                option_var.set(cat)
                                current_data[cat].remove(value)
                                refresh_list()
                            return _edit

                        def make_remove(cat, value):
                            def _remove():
                                current_data[cat].remove(value)
                                refresh_list()
                            return _remove

                        ctk.CTkButton(
                            inner, text="Edit", width=52, height=24,
                            corner_radius=6, fg_color=colors["secondary"],
                            hover_color=colors["primary"], text_color=colors["surface"],
                            font=("Georgia", 11),
                            command=make_edit(k, val)
                        ).pack(side="right", padx=(0, 4))

                        ctk.CTkButton(
                            inner, text="Remove", width=66, height=24,
                            corner_radius=6, fg_color="#6B6B6B", hover_color="#4A4A4A",
                            text_color=colors["surface"], font=("Georgia", 11),
                            command=make_remove(k, val)
                        ).pack(side="right", padx=(4, 4))

                if not has_any:
                    ctk.CTkLabel(
                        list_frame,
                        text="No note filters added yet.",
                        text_color=colors["secondary"],
                        font=("Georgia", 11, "italic")
                    ).pack(pady=8)

            # json extraction
            def _get_json():
                if not any(current_data.values()):
                    return False, None
                return True, current_data

            refresh_list()

            widget = {
                "input_var": input_var,
                "option_var": option_var,
                "data": current_data,
                "_get_json": _get_json,
            }
            self.entries[field] = widget

        elif field == "feedback-comment":
        
            container = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=12)
            container.pack(fill="x", padx=10, pady=(0, 10))

            raw_data = self.optional_data.get(field)
            if not isinstance(raw_data, dict):
                current_data = {"and": [], "nor": []}
            else:
                current_data = {"and": [], "nor": []}
                for k in ("and", "nor"):
                    items = raw_data.get(k, [])
                    for it in items:
                        if isinstance(it, dict) and "val" in it:
                            current_data[k].append(it)
                        elif isinstance(it, str):
                            current_data[k].append({"val": it, "exists": "true"})

            input_frame = ctk.CTkFrame(container, fg_color="transparent")
            input_frame.pack(fill="x", padx=10, pady=(8, 6))

            input_var = tk.StringVar()
            input_entry = ctk.CTkEntry(
                input_frame, placeholder_text="Enter feedback keyword",
                textvariable=input_var, width=220, height=32, corner_radius=8,
                font=("Georgia", 12)
            )
            input_entry.pack(side="left", padx=(0, 6))

            option_var = tk.StringVar(value="and")
            option_menu = ctk.CTkOptionMenu(
                input_frame, variable=option_var, values=["and", "nor"],  # ❗ NO OR
                width=90, height=32, corner_radius=8,
                fg_color=colors["primary"], button_color=colors["primary"],
                button_hover_color=colors["secondary"], text_color=colors["surface"],
                font=("Georgia", 12)
            )
            option_menu.pack(side="left", padx=(0, 6))

            exists_var = tk.StringVar(value=current_data.get("exists", "true"))
            exists_menu = ctk.CTkOptionMenu(
                input_frame, variable=exists_var, values=["true", "false"],
                width=90, height=32, corner_radius=8,
                fg_color=colors["primary"], button_color=colors["primary"],
                button_hover_color=colors["secondary"], text_color=colors["surface"],
                font=("Georgia", 12)
            )
            exists_menu.pack(side="left", padx=(0, 6))

            def add_item():
                text = input_var.get().strip()
                if not text:
                    return
                cat = option_var.get()
                item = {"val": text, "exists": exists_var.get()}
                if item not in current_data.get(cat, []):
                    current_data.setdefault(cat, []).append(item)
                input_var.set("")
                refresh_list()

            add_btn = ctk.CTkButton(
                input_frame, text="Add", width=70, height=32,
                fg_color=colors["primary"], hover_color=colors["secondary"],
                text_color=colors["surface"], font=("Georgia", 12),
                command=add_item
            )
            add_btn.pack(side="left", padx=(4, 0))
            # list section
            list_frame = ctk.CTkFrame(container, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=12, pady=(6, 4))

            def refresh_list():
                for child in list_frame.winfo_children():
                    child.destroy()

                has_any = False

                for k in ("and", "nor"):

                    for item in list(current_data.get(k, [])):
                        val = item.get("val")
                        exists_txt = item.get("exists", "true")

                        has_any = True

                        row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                        row.pack(fill="x", padx=6, pady=3)

                        inner = ctk.CTkFrame(row, fg_color="transparent")
                        inner.pack(fill="x", padx=10, pady=4)

                        text_display = f"{k.upper()} → {val}   (exists: {exists_txt})"
                        label = ctk.CTkLabel(
                            inner, text=text_display, anchor="w", justify="left",
                            text_color=colors["primary"], font=("Georgia", 12), wraplength=330
                        )
                        label.pack(side="left", fill="x", expand=True, padx=(0, 6))

                
                            
                        
                        def make_edit(cat, itm):
                            def _edit():
                                input_var.set(itm["val"])
                                option_var.set(cat)
                                exists_var.set(itm.get("exists", "true"))
                                current_data[cat].remove(itm)
                                refresh_list()
                            return _edit

                        def make_remove(cat, itm):
                            def _remove():
                                current_data[cat].remove(itm)
                                refresh_list()
                            return _remove

                        ctk.CTkButton(
                            inner, text="Edit", width=52, height=24,
                            corner_radius=6, fg_color=colors["secondary"],
                            hover_color=colors["primary"], text_color=colors["surface"],
                            font=("Georgia", 11),
                            command=make_edit(k, item)
                        ).pack(side="right", padx=(0, 4))

                        ctk.CTkButton(
                            inner, text="Remove", width=66, height=24,
                            corner_radius=6, fg_color="#6B6B6B", hover_color="#4A4A4A",
                            text_color=colors["surface"], font=("Georgia", 11),
                            command=make_remove(k, item)
                        ).pack(side="right", padx=(4, 4))

                if not has_any:
                    ctk.CTkLabel(
                        list_frame,
                        text="No feedback filters added yet.",
                        text_color=colors["secondary"],
                        font=("Georgia", 11, "italic")
                    ).pack(pady=8)

     

            def _get_json():
                payload = {}

                if current_data.get("and"):
                    payload["and"] = [i["val"] for i in current_data["and"] if i.get("exists") == "true"]

                if current_data.get("nor"):
                    payload["nor"] = [i["val"] for i in current_data["nor"] if i.get("exists") == "true"]

                if not payload:
                    return False, None
                return True, payload

            refresh_list()

            widget = {
                "input_var": input_var,
                "option_var": option_var,
                "exists_var": exists_var,
                "data": current_data,
                "_get_json": _get_json,
            }

            self.entries[field] = widget

        elif field == "excludes":
            container = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=12)
            container.pack(fill="x", padx=10, pady=(0, 10))
            raw_data = self.optional_data.get(field)
            if not isinstance(raw_data, list):
                current_data = []
            else:
                current_data = list(raw_data)
            input_frame = ctk.CTkFrame(container, fg_color="transparent")
            input_frame.pack(fill="x", padx=10, pady=(8, 6))
            input_var = tk.StringVar()
            input_entry = ctk.CTkEntry(
                input_frame, placeholder_text="Enter field to exclude (e.g. messages)",
                textvariable=input_var, width=260, height=32, corner_radius=8,
                font=("Georgia", 12)
            )
            input_entry.pack(side="left", padx=(0, 6))
           
            def add_item():
                text = input_var.get().strip()
                if not text:
                    return
                values = [v.strip() for v in text.split(",") if v.strip()]
                for v in values:
                    if v not in current_data:
                        current_data.append(v)
                input_var.set("")
                refresh_list()

            add_btn = ctk.CTkButton(
                input_frame, text="Add", width=70, height=32,
                fg_color=colors["primary"], hover_color=colors["secondary"],
                text_color=colors["surface"], font=("Georgia", 12),
                command=add_item
            )
            add_btn.pack(side="left", padx=(4, 0))
            # list section
            list_frame = ctk.CTkFrame(container, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=12, pady=(6, 4))
            def refresh_list():
                for child in list_frame.winfo_children():
                    child.destroy()
                if not current_data:
                    ctk.CTkLabel(
                        list_frame,
                        text="No excluded fields added yet.",
                        text_color=colors["secondary"],
                        font=("Georgia", 11, "italic")
                    ).pack(pady=8)
                    return
                for val in list(current_data):
                    row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                    row.pack(fill="x", padx=6, pady=3)
                    inner = ctk.CTkFrame(row, fg_color="transparent")
                    inner.pack(fill="x", padx=10, pady=4)
                    label = ctk.CTkLabel(
                        inner, text=val, anchor="w", justify="left",
                        text_color=colors["primary"], font=("Georgia", 12), wraplength=360
                    )
                    label.pack(side="left", fill="x", expand=True, padx=(0, 6))
                    def make_edit(value):
                        def _edit():
                            input_var.set(value)
                            current_data.remove(value)
                            refresh_list()
                        return _edit
                    def make_remove(value):
                        def _remove():
                            current_data.remove(value)
                            refresh_list()
                        return _remove
                    ctk.CTkButton(
                        inner, text="Edit", width=52, height=24,
                        corner_radius=6, fg_color=colors["secondary"],
                        hover_color=colors["primary"], text_color=colors["surface"],
                        font=("Georgia", 11),
                        command=make_edit(val)
                    ).pack(side="right", padx=(0, 4))
                    ctk.CTkButton(
                        inner, text="Remove", width=66, height=24,
                        corner_radius=6, fg_color="#6B6B6B", hover_color="#4A4A4A",
                        text_color=colors["surface"], font=("Georgia", 11),
                        command=make_remove(val)
                    ).pack(side="right", padx=(4, 4))
            # json extraction
            def _get_json():
                if not current_data:
                    return False, None
                return True, current_data
            refresh_list()
            widget = {
                "input_var": input_var,
                "data": current_data,
                "_get_json": _get_json,
            }
            self.entries[field] = widget

        elif field == "issue_modes":
        
            container = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=12)
            container.pack(fill="x", padx=10, pady=(0, 10))

            raw_data = self.optional_data.get(field)
            if not isinstance(raw_data, list):
                current_data = []
            else:
                current_data = list(raw_data)

            input_frame = ctk.CTkFrame(container, fg_color="transparent")
            input_frame.pack(fill="x", padx=10, pady=(8, 6))

            input_var = tk.StringVar()
            input_entry = ctk.CTkEntry(
                input_frame, placeholder_text="Enter issue mode (e.g. proactive, chat)",
                textvariable=input_var, width=260, height=32, corner_radius=8,
                font=("Georgia", 12)
            )
            input_entry.pack(side="left", padx=(0, 6))

           
            def add_item():
                text = input_var.get().strip()
                if not text:
                    return
                values = [v.strip() for v in text.split(",") if v.strip()]
                for v in values:
                    if v not in current_data:
                        current_data.append(v)
                input_var.set("")
                refresh_list()

            add_btn = ctk.CTkButton(
                input_frame, text="Add", width=70, height=32,
                fg_color=colors["primary"], hover_color=colors["secondary"],
                text_color=colors["surface"], font=("Georgia", 12),
                command=add_item
            )
            add_btn.pack(side="left", padx=(4, 0))

            list_frame = ctk.CTkFrame(container, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=12, pady=(6, 4))

            def refresh_list():
                for child in list_frame.winfo_children():
                    child.destroy()

                if not current_data:
                    ctk.CTkLabel(
                        list_frame,
                        text="No issue modes added yet.",
                        text_color=colors["secondary"],
                        font=("Georgia", 11, "italic")
                    ).pack(pady=8)
                    return

                for val in list(current_data):
                    row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                    row.pack(fill="x", padx=6, pady=3)

                    inner = ctk.CTkFrame(row, fg_color="transparent")
                    inner.pack(fill="x", padx=10, pady=4)

                    label = ctk.CTkLabel(
                        inner, text=val, anchor="w", justify="left",
                        text_color=colors["primary"], font=("Georgia", 12), wraplength=360
                    )
                    label.pack(side="left", fill="x", expand=True, padx=(0, 6))

                    def make_edit(value):
                        def _edit():
                            input_var.set(value)
                            current_data.remove(value)
                            refresh_list()
                        return _edit

                    def make_remove(value):
                        def _remove():
                            current_data.remove(value)
                            refresh_list()
                        return _remove

                    ctk.CTkButton(
                        inner, text="Edit", width=52, height=24,
                        corner_radius=6, fg_color=colors["secondary"],
                        hover_color=colors["primary"], text_color=colors["surface"],
                        font=("Georgia", 11),
                        command=make_edit(val)
                    ).pack(side="right", padx=(0, 4))

                    ctk.CTkButton(
                        inner, text="Remove", width=66, height=24,
                        corner_radius=6, fg_color="#6B6B6B", hover_color="#4A4A4A",
                        text_color=colors["surface"], font=("Georgia", 11),
                        command=make_remove(val)
                    ).pack(side="right", padx=(4, 4))

            def _get_json():
                if not current_data:
                    return False, None
                return True, current_data

            refresh_list()

            widget = {
                "input_var": input_var,
                "data": current_data,
                "_get_json": _get_json,
            }

            self.entries[field] = widget

        elif field == "page":
        
            container = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=12)
            container.pack(fill="x", padx=10, pady=(0, 10))

            raw_data = self.optional_data.get(field)
            current_value = str(raw_data) if raw_data is not None else ""

            input_frame = ctk.CTkFrame(container, fg_color="transparent")
            input_frame.pack(fill="x", padx=10, pady=(8, 6))

            input_var = tk.StringVar(value=current_value)
            input_entry = ctk.CTkEntry(
                input_frame, placeholder_text="Enter page number (integer)",
                textvariable=input_var, width=260, height=32, corner_radius=8,
                font=("Georgia", 12)
            )
            input_entry.pack(side="left", padx=(0, 6))

            def add_item():
                val = input_var.get().strip()
                if not val.isdigit() or int(val) <= 0:
                    messagebox.showerror("Invalid Input", "Page must be a positive integer.")
                    input_entry.focus_set()
                    input_entry.selection_range(0, "end")
                    return

                # page-size check if exists
                ps = self.entries.get("page-size")
                if ps and ps.get("data"):
                    try:
                        ps_val = int(ps["data"][0])
                        if int(val) * ps_val > 50000:
                            messagebox.showerror(
                                "Invalid Pagination",
                                "page × page-size must not exceed 50000."
                            )
                            
                            return
                    except:
                        pass
                    
                current_data.clear()
                current_data.append(val)
                refresh_list()

            add_btn = ctk.CTkButton(
                input_frame, text="Add / Update", width=90, height=32,
                fg_color=colors["primary"], hover_color=colors["secondary"],
                text_color=colors["surface"], font=("Georgia", 12),
                command=add_item
            )
            add_btn.pack(side="left", padx=(4, 0))

            list_frame = ctk.CTkFrame(container, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=12, pady=(6, 4))

            current_data = []
            if current_value:
                current_data.append(current_value)

            def refresh_list():
                for child in list_frame.winfo_children():
                    child.destroy()

                if not current_data:
                    ctk.CTkLabel(
                        list_frame, text="No page selected.",
                        text_color=colors["secondary"], font=("Georgia", 11, "italic")
                    ).pack(pady=8)
                    return

                val = current_data[0]
                row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                row.pack(fill="x", padx=6, pady=3)

                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=4)

                label = ctk.CTkLabel(
                    inner, text=f"Page: {val}",
                    text_color=colors["primary"], font=("Georgia", 12)
                )
                label.pack(side="left", expand=True, fill="x")

                def remove_item():
                    current_data.clear()
                    input_var.set("")
                    refresh_list()

                ctk.CTkButton(
                    inner, text="Remove", width=70, height=24,
                    corner_radius=6, fg_color="#6B6B6B", hover_color="#4A4A4A",
                    text_color=colors["surface"], font=("Georgia", 11),
                    command=remove_item
                ).pack(side="right")

            def _get_json():
                if not current_data:
                    return False, None
                return True, int(current_data[0])

            refresh_list()

            widget = {
                "input_var": input_var,
                "data": current_data,
                "_get_json": _get_json,
            }

            self.entries[field] = widget

        elif field == "page-size":
            container = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=12)
            container.pack(fill="x", padx=10, pady=(0, 10))
            raw_data = self.optional_data.get(field)
            current_value = str(raw_data) if raw_data is not None else ""
            input_frame = ctk.CTkFrame(container, fg_color="transparent")
            input_frame.pack(fill="x", padx=10, pady=(8, 6))
            input_var = tk.StringVar(value=current_value)
            input_entry = ctk.CTkEntry(
                input_frame, placeholder_text="Enter page size (1–1000)",
                textvariable=input_var, width=260, height=32, corner_radius=8,
                font=("Georgia", 12)
            )
            input_entry.pack(side="left", padx=(0, 6))
            current_data = []
            if current_value:
                current_data.append(current_value)
            def add_item():
                val = input_var.get().strip()
                if not val.isdigit():
                    messagebox.showerror("Invalid Input", "Page-size must be a number.")
                    refocus()
                    return
                val_i = int(val)
                if not (1 <= val_i <= 1000):
                    messagebox.showerror("Invalid Input", "Page-size must be between 1 and 1000.")
                    refocus()
                    return
                # page check if exists
                p = self.entries.get("page")
                if p and p.get("data"):
                    try:
                        p_val = int(p["data"][0])
                        if p_val * val_i > 50000:
                            messagebox.showerror(
                                "Invalid Pagination",
                                "page × page-size must not exceed 50000."
                            )
                            refocus()
                            return
                    except:
                        pass
                current_data.clear()
                current_data.append(val)
                refresh_list()
            add_btn = ctk.CTkButton(
                input_frame, text="Add / Update", width=90, height=32,
                fg_color=colors["primary"], hover_color=colors["secondary"],
                text_color=colors["surface"], font=("Georgia", 12),
                command=add_item
            )
            add_btn.pack(side="left", padx=(4, 0))
            list_frame = ctk.CTkFrame(container, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=12, pady=(6, 4))
            def refresh_list():
                for child in list_frame.winfo_children():
                    child.destroy()
                if not current_data:
                    ctk.CTkLabel(
                        list_frame, text="No page size selected.",
                        text_color=colors["secondary"], font=("Georgia", 11, "italic")
                    ).pack(pady=8)
                    return
                val = current_data[0]
                row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                row.pack(fill="x", padx=6, pady=3)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=4)
                label = ctk.CTkLabel(
                    inner, text=f"Page Size: {val}",
                    text_color=colors["primary"], font=("Georgia", 12)
                )
                label.pack(side="left", expand=True, fill="x")
                def remove_item():
                    current_data.clear()
                    input_var.set("")
                    refresh_list()
                ctk.CTkButton(
                    inner, text="Remove", width=70, height=24,
                    corner_radius=6, fg_color="#6B6B6B", hover_color="#4A4A4A",
                    text_color=colors["surface"], font=("Georgia", 11),
                    command=remove_item
                ).pack(side="right")
            def _get_json():
                if not current_data:
                    return False, None
                return True, int(current_data[0])
            refresh_list()
            widget = {
                "input_var": input_var,
                "data": current_data,
                "_get_json": _get_json,
            }
            
            
            def _get_json():
                if not current_data:
                    return False, None
                return True, int(current_data[0])
            
            widget = {
                "data": current_data,
                "_get_json": _get_json
            }
            
            self.entries[field] = widget
            
        elif field in {"state_since", "state-until", "updated_until", "updated_since"}:
        
            container = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=12)
            container.pack(fill="x", padx=10, pady=(0, 10))
        
            raw_data = self.optional_data.get(field)
            current_value = str(raw_data) if raw_data is not None else ""
        
            input_frame = ctk.CTkFrame(container, fg_color="transparent")
            input_frame.pack(fill="x", padx=10, pady=(8, 6))
        
            input_var = tk.StringVar(value=current_value)
            input_entry = ctk.CTkEntry(
                input_frame,
                placeholder_text="Enter unix timestamp in milliseconds",
                textvariable=input_var, width=280, height=32, corner_radius=8,
                font=("Georgia", 12)
            )
            input_entry.pack(side="left", padx=(0, 6))
        
            current_data = []
            if current_value:
                current_data.append(current_value)
        
            def refocus():
                input_entry.after(50, lambda: (
                    input_entry.focus_set(),
                    input_entry.selection_range(0, "end")
                ))
        
            def add_item():
                val = input_var.get().strip()
        
                if not val.isdigit():
                    messagebox.showerror("Invalid Input", "Timestamp must be a number (unix ms).")
                    refocus()
                    return
        
                if len(val) < 13:   # ms timestamp should be 13 digits
                    messagebox.showerror("Invalid Input", "Timestamp must be in milliseconds (13 digits).")
                    refocus()
                    return
        
                current_data.clear()
                current_data.append(int(val))
                refresh_list()
        
            add_btn = ctk.CTkButton(
                input_frame, text="Add / Update", width=90, height=32,
                fg_color=colors["primary"], hover_color=colors["secondary"],
                text_color=colors["surface"], font=("Georgia", 12),
                command=add_item
            )
            add_btn.pack(side="left", padx=(4, 0))
        
            list_frame = ctk.CTkFrame(container, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=12, pady=(6, 4))
        
            def refresh_list():
                for child in list_frame.winfo_children():
                    child.destroy()
        
                if not current_data:
                    ctk.CTkLabel(
                        list_frame,
                        text="No timestamp selected.",
                        text_color=colors["secondary"],
                        font=("Georgia", 11, "italic")
                    ).pack(pady=8)
                    return
        
                val = current_data[0]
        
                row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                row.pack(fill="x", padx=6, pady=3)
        
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=4)
        
                label = ctk.CTkLabel(
                    inner, text=val,
                    text_color=colors["primary"], font=("Georgia", 12)
                )
                label.pack(side="left", expand=True, fill="x")
        
                def remove_item():
                    current_data.clear()
                    input_var.set("")
                    refresh_list()
        
                ctk.CTkButton(
                    inner, text="Remove", width=70, height=24,
                    corner_radius=6, fg_color="#6B6B6B", hover_color="#4A4A4A",
                    text_color=colors["surface"], font=("Georgia", 11),
                    command=remove_item
                ).pack(side="right")
        
            def _get_json():
                if not current_data:
                    return False, None
                return True, int(current_data[0])
        
            refresh_list()
        
            widget = {
                "input_var": input_var,
                "data": current_data,
                "_get_json": _get_json,
            }
        
            self.entries[field] = widget
        
        elif field == "timestamp-format":
                    widget = ctk.CTkOptionMenu(
                        body, values=["","unix", "iso-8601"], width=250, corner_radius=8,
                        font=ctk.CTkFont(family="Georgia", size=14),
                        fg_color=colors["primary"], button_color=colors["primary"],
                        button_hover_color=colors["secondary"], text_color=colors["surface"]
                    )
                    widget.set(self.optional_data.get(field, ""))
                    widget.pack(padx=10, pady=10, anchor="w")

                    def _get_json():
                        val = widget.get()
                        if val in ("", None):
                            return True, None
                        return True, val

                    self.entries[field] = {
                        "widget": widget,
                        "_get_json": _get_json
                    }
                
        elif field == "redacted":
                    widget = ctk.CTkOptionMenu(
                        body, values=["","true", "false"], width=250, corner_radius=8,
                        font=ctk.CTkFont(family="Georgia", size=14),
                        fg_color=colors["primary"], button_color=colors["primary"],
                        button_hover_color=colors["secondary"], text_color=colors["surface"]
                    )
                    widget.set(self.optional_data.get(field, ""))
                    widget.pack(padx=10, pady=10, anchor="w")

                    def _get_json():
                        val = widget.get()
                        if val in ("", None):
                            return True, None
                        return True, val

                    self.entries[field] = {
                        "widget": widget,
                        "_get_json": _get_json
                    }

        elif field == "includes":
            selected = self.optional_data.get("includes", [])
            btn_var = ctk.StringVar(value=", ".join(selected) if selected else "Select includes...")

            checkbox_frame = ctk.CTkFrame(body, fg_color="transparent")
            checkbox_frame.pack(fill="x", padx=10, pady=(0, 10))

            vars_dict = {}
            for opt in INCLUDES_OPTIONS:
                var = ctk.BooleanVar(value=(opt in selected))
                chk = ctk.CTkCheckBox(
                    checkbox_frame,
                    text=opt,
                    variable=var,
                    text_color=colors["primary"],
                    font=ctk.CTkFont(family="Georgia", size=13),
                    corner_radius=6,
                    border_width=1,
                    checkbox_width=16,
                    checkbox_height=16
                )
                chk.pack(anchor="w", pady=2, padx=10)
                vars_dict[opt] = var

            # --- Auto-update selected string ---
            def update_selection(*_):
                selected_opts = [k for k, v in vars_dict.items() if v.get()]
                btn_var.set(", ".join(selected_opts) if selected_opts else "Select includes...")

            for v in vars_dict.values():
                v.trace_add("write", update_selection)

            update_selection()

            def _get_json():
                selected_opts = [k for k, v in vars_dict.items() if v.get()]
                return True, selected_opts

            widget = {
                "vars": vars_dict,
                "_get_json": _get_json
            }

            self.entries[field] = widget

        elif field == "app-ids":
            selected = self.optional_data.get(field, [])
            if isinstance(selected, str):
                try:
                    selected = json.loads(selected)
                except Exception:
                    selected = [selected]
            if not isinstance(selected, list):
                selected = [str(selected)]
            selected = [str(x) for x in selected if x]

            if selected:
                btn_text = f"{len(selected)} app(s) selected" if len(selected) > 1 else selected[0]
            else:
                btn_text = "Select app(s)..."
            btn_var = ctk.StringVar(value=btn_text)

            dropdown_btn = ctk.CTkButton(
                body,
                textvariable=btn_var,
                width=400,
                height=36,
                corner_radius=8,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=13),
            )
            dropdown_btn.pack(pady=(0, 10), padx=10)

            dropdown_frame = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=8)
            dropdown_frame.pack_forget()
            search_var = tk.StringVar()
            search_entry = ctk.CTkEntry(
                dropdown_frame,
                placeholder_text="Search app by id or name...",
                textvariable=search_var,
                width=380,
                height=32,
                font=ctk.CTkFont(family="Georgia", size=12),
            )
            search_entry.pack(padx=10, pady=(8, 6))

            actions_row = ctk.CTkFrame(dropdown_frame, fg_color="transparent")
            actions_row.pack(fill="x", padx=10, pady=(0, 6))
            select_all_btn = ctk.CTkButton(
                actions_row,
                text="Select All",
                width=110,
                height=28,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                font=ctk.CTkFont(family="Georgia", size=11),
            )
            clear_all_btn = ctk.CTkButton(
                actions_row,
                text="Clear All",
                width=110,
                height=28,
                fg_color="#E5E5E5",
                hover_color=colors["secondary"],
                text_color=colors["primary"],
                font=ctk.CTkFont(family="Georgia", size=11),
            )
            select_all_btn.pack(side="left", padx=(0, 6))
            clear_all_btn.pack(side="left")

            checkbox_frame = ctk.CTkScrollableFrame(
                dropdown_frame,
                fg_color="transparent",
                width=400,
                height=220
            )
            checkbox_frame.pack(padx=10, pady=(6, 10))
            vars_dict = {}
            all_apps = []


            def fetch_apps():
                nonlocal all_apps
                try:
                    res = requests.get(f"{API_BASE_URL}/fetch-apps/")
                    print("fetch-apps status:", res.status_code)
                    if res.status_code == 200:
                        data = res.json()
                        apps = data.get("apps", []) or []
                        if isinstance(apps, dict):
                            apps = apps.get("apps", []) or []
                        # Filter out Web apps
                        apps = [app for app in apps if app.get("title") != "Web"]
                        all_apps = apps
                    else:
                        all_apps = []
                        print("fetch-apps returned non-200:", res.text)
                except Exception as e:
                    print("fetch-apps error:", e)
                    all_apps = []

            def render_checkboxes(filter_text=""):
                for w in checkbox_frame.winfo_children():
                    w.destroy()
                vars_dict.clear()
                ft = (filter_text or "").strip().lower()
                filtered = [
                    app for app in all_apps
                    if not ft
                    or ft in str(app.get("id", "")).lower()
                    or ft in (app.get("title") or "").lower()
                    or ft in (app.get("name") or "").lower()
                ]
                if not filtered:
                    ctk.CTkLabel(checkbox_frame, text="No apps found", text_color="red").pack(pady=6)
                    return
                for app in filtered:
                    app_id = str(app.get("id", ""))
                    app_name = app.get("title") or app.get("name") or "Unknown"
                    # Restore selection from previous state
                    var = tk.BooleanVar(value=(app_id in selected))
                    chk = ctk.CTkCheckBox(
                        checkbox_frame,
                        text=app_name,  
                        variable=var,
                        text_color=colors["primary"],
                        font=ctk.CTkFont(family="Georgia", size=12),
                        border_width=1,
                        corner_radius=6,
                        checkbox_width=16,
                        checkbox_height=16,
                    )
                    chk.pack(anchor="w", pady=2, padx=4)
                    vars_dict[app_id] = var
                    var.trace_add("write", lambda *_, app_id=app_id: update_selection())
                update_selection()

            def update_selection():
                chosen_ids = [app_id for app_id, v in vars_dict.items() if bool(v.get())]
                total = len(vars_dict)
                chosen_count = len(chosen_ids)
                if total > 0 and chosen_count == total:
                    btn_var.set("All Apps Selected")
                elif chosen_count > 0:
                    btn_var.set(f"{chosen_count} app(s) selected")
                else:
                    btn_var.set("Select app(s)...")
                self.optional_data[field] = chosen_ids

            def select_all():
                for v in vars_dict.values():
                    v.set(True)
                update_selection()
            def clear_all():
                for v in vars_dict.values():
                    v.set(False)
                update_selection()
            select_all_btn.configure(command=select_all)
            clear_all_btn.configure(command=clear_all)
            
            def open_dropdown():
                if not dropdown_frame.winfo_ismapped():
                    dropdown_frame.pack(padx=10, pady=(0, 10), anchor="w", fill="x")
                    if not all_apps:
                        fetch_apps()
                    render_checkboxes(filter_text="")
                    # :white_check_mark: Bind search *after* apps are loaded
                    search_var.trace_add("write", lambda *args: render_checkboxes(filter_text=search_var.get()))
            def close_dropdown():
                if dropdown_frame.winfo_ismapped():
                    dropdown_frame.pack_forget()
            def toggle_dropdown():
                if dropdown_frame.winfo_ismapped():
                    close_dropdown()
                else:
                    open_dropdown()
            dropdown_btn.configure(command=toggle_dropdown)
          
            def _get_json():
                selected_now = self.optional_data.get(field, [])

                if not isinstance(selected_now, list):
                    selected_now = []

                return True, selected_now
            widget = {
                "frame": dropdown_frame,
                "btn_var": btn_var,
                "vars_dict": vars_dict,
                "_get_json": _get_json,
            }
            self.entries[field] = widget

        elif field == "queue_ids":
            selected = self.optional_data.get(field, [])
            if isinstance(selected, str):
                selected = [selected]
            selected = [str(x) for x in selected]
            btn_var = ctk.StringVar(value=", ".join(selected) if selected else "Select queues...")
            
            dropdown_btn = ctk.CTkButton(
                body,
                textvariable=btn_var,
                width=400,
                height=36,
                corner_radius=8,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=13),
            )
            dropdown_btn.pack(pady=(0, 10), padx=10)
            
            dropdown_frame = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=8)
            dropdown_frame.pack_forget()
            
            search_var = tk.StringVar()
            search_entry = ctk.CTkEntry(
                dropdown_frame,
                placeholder_text="Search queue by id or name...",
                textvariable=search_var,
                width=380,
                height=32,
                font=ctk.CTkFont(family="Georgia", size=12),
            )
            search_entry.pack(padx=10, pady=(8, 6))
            
            actions_row = ctk.CTkFrame(dropdown_frame, fg_color="transparent")
            actions_row.pack(fill="x", padx=10, pady=(0, 6))
            select_all_btn = ctk.CTkButton(
                actions_row,
                text="Select All",
                width=110,
                height=28,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                font=ctk.CTkFont(family="Georgia", size=11),
            )
            clear_all_btn = ctk.CTkButton(
                actions_row,
                text="Clear All",
                width=110,
                height=28,
                fg_color="#E5E5E5",
                hover_color=colors["secondary"],
                text_color=colors["primary"],
                font=ctk.CTkFont(family="Georgia", size=11),
            )
            select_all_btn.pack(side="left", padx=(0, 6))
            clear_all_btn.pack(side="left")
            
            checkbox_frame = ctk.CTkScrollableFrame(
                dropdown_frame,
                fg_color="transparent",
                width=400,
                height=220
            )
            checkbox_frame.pack(padx=10, pady=(6, 10))
            vars_dict = {}
            all_queues = []
           
            def fetch_queues():
                nonlocal all_queues
                try:
                    res = requests.get(f"{API_BASE_URL}/fetch-queues/")
                    print("fetch-queues status:", res.status_code)
                    if res.status_code == 200:
                        data = res.json()
                        queues = data.get("queues", []) or []
                        if isinstance(queues, dict):
                            queues = queues.get("queues", []) or []
                        all_queues = queues
                    else:
                        all_queues = []
                        print("fetch-queues returned non-200:", res.text)
                except Exception as e:
                    print("fetch-queues error:", e)
                    all_queues = []
            
            def render_checkboxes(filter_text=""):
                for w in checkbox_frame.winfo_children():
                    w.destroy()
                vars_dict.clear()
                ft = (filter_text or "").strip().lower()
                filtered = [
                    q for q in all_queues
                    if not ft or ft in str(q.get("id", "")).lower() or ft in (q.get("title") or "").lower()
                ]
                if not filtered:
                    ctk.CTkLabel(checkbox_frame, text="No queues found", text_color="red").pack(pady=6)
                    return
                for q in filtered:
                    qid = str(q.get("id", ""))
                    qname = q.get("title") or q.get("name") or "Unknown"
                    # :white_check_mark: All selected by default
                    var = tk.BooleanVar(value=True)
                    chk = ctk.CTkCheckBox(
                        checkbox_frame,
                        text=qname,
                        variable=var,
                        text_color=colors["primary"],
                        font=ctk.CTkFont(family="Georgia", size=12),
                        border_width=1,
                        corner_radius=6,
                        checkbox_width=16,
                        checkbox_height=16,
                    )
                    chk.pack(anchor="w", pady=2, padx=4)
                    vars_dict[qid] = var
                    var.trace_add("write", lambda *_, qid=qid: update_selection())
                update_selection()
            
            def update_selection():
                chosen_ids = [qid for qid, v in vars_dict.items() if bool(v.get())]
                total = len(vars_dict)
                chosen_count = len(chosen_ids)
                if total > 0 and chosen_count == total:
                    btn_var.set("All Queues Selected")
                elif chosen_count > 0:
                    btn_var.set(f"{chosen_count} queue(s) selected")
                else:
                    btn_var.set("Select queues...")
                self.optional_data[field] = chosen_ids
            
            def select_all():
                for v in vars_dict.values():
                    v.set(True)
                update_selection()
            def clear_all():
                for v in vars_dict.values():
                    v.set(False)
                update_selection()
            select_all_btn.configure(command=select_all)
            clear_all_btn.configure(command=clear_all)
            
            def open_dropdown():
                if not dropdown_frame.winfo_ismapped():
                    dropdown_frame.pack(padx=10, pady=(0, 10), anchor="w", fill="x")
                    if not all_queues:
                        fetch_queues()
                    render_checkboxes(filter_text="")
                    # :white_check_mark: Bind search *after* queues are loaded
                    search_var.trace_add("write", lambda *args: render_checkboxes(filter_text=search_var.get()))
            def close_dropdown():
                if dropdown_frame.winfo_ismapped():
                    dropdown_frame.pack_forget()
            def toggle_dropdown():
                if dropdown_frame.winfo_ismapped():
                    close_dropdown()
                else:
                    open_dropdown()
            dropdown_btn.configure(command=toggle_dropdown)
            
            
            def _get_json(show_warning=False):

                selected_now = self.optional_data.get(field, [])

                if not selected_now:
                
                    if show_warning:
                        from CTkMessagebox import CTkMessagebox
                        CTkMessagebox(
                            title="No Queues Selected",
                            message="Please select at least one queue before exporting.",
                            icon="warning",
                            option_1="OK"
                        )

                    return False, {}

                return True, selected_now
            
            widget = {
                "frame": dropdown_frame,
                "btn_var": btn_var,
                "vars_dict": vars_dict,
                "_get_json": _get_json,
            }
            self.entries[field] = widget

        elif field in ["state", "platform-types"]:
        
            if field == "state":
                options = [
                    "new", "new-for-agent", "agent-replied", "waiting-for-agent",
                    "resolved", "rejected", "pending-reassignment"
                ]
            else:  
                options = ["ios", "android", "email", "web", "webchat"]

            selected = self.optional_data.get(field, [])

            if isinstance(selected, str):
                selected = [s.strip() for s in selected.split(",") if s.strip()]
            elif not isinstance(selected, list):
                selected = []

            vars_dict = {}

            checkbox_frame = ctk.CTkFrame(body, fg_color="transparent")
            checkbox_frame.pack(fill="x", padx=10, pady=(0, 10))

            for opt in options:
                var = ctk.BooleanVar(value=(opt in selected))
                chk = ctk.CTkCheckBox(
                    checkbox_frame,
                    text=opt,
                    variable=var,
                    text_color=colors["primary"],
                    font=ctk.CTkFont(family="Georgia", size=13),
                    corner_radius=6,
                    border_width=1,
                    checkbox_width=16,
                    checkbox_height=16
                )
                chk.pack(anchor="w", pady=2, padx=10)
                vars_dict[opt] = var

            def _get_json():
                selected_opts = [k for k, v in vars_dict.items() if v.get()]
                return True, selected_opts

            self.entries[field] = {
                "vars": vars_dict,
                "_get_json": _get_json
            }

        elif field == "end-user-ids":
           
            end_user_frame = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=10)
            end_user_frame.pack(padx=10, pady=(5, 10), fill="x")

            input_row = ctk.CTkFrame(end_user_frame, fg_color="transparent")
            input_row.pack(fill="x", padx=10, pady=(0, 6))

            end_user_entry = ctk.CTkEntry(
                input_row,
                width=400,
                corner_radius=8,
                placeholder_text="Enter end user IDs (comma-separated)",
                fg_color=colors["surface"],
                border_color=colors["primary"],
                text_color=colors["primary"],
                font=ctk.CTkFont(family="Georgia", size=13)
            )
            end_user_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

            add_btn = ctk.CTkButton(
                input_row,
                text="Add",
                width=80,
                height=32,
                corner_radius=8,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=12)
            )
            add_btn.pack(side="right")

            list_frame = ctk.CTkFrame(end_user_frame, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=10, pady=(8, 4))

            end_user_ids = []  

            empty_label = ctk.CTkLabel(
                list_frame,
                text="No end user ID added yet.",
                text_color=colors["secondary"],
                font=ctk.CTkFont(family="Georgia", size=12, slant="italic")
            )
            empty_label.pack(pady=10)

            def refresh_list():
                for w in list_frame.winfo_children():
                    w.destroy()

                if not end_user_ids:
                    empty_label = ctk.CTkLabel(
                        list_frame,
                        text="No end user ID added yet.",
                        text_color=colors["secondary"],
                        font=ctk.CTkFont(family="Georgia", size=12, slant="italic")
                    )
                    empty_label.pack(pady=10)
                    return

                for uid in end_user_ids:
                    item_row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                    item_row.pack(fill="x", padx=6, pady=4)

                    lbl = ctk.CTkLabel(
                        item_row,
                        text=uid,
                        text_color=colors["primary"],
                        anchor="w",
                        font=ctk.CTkFont(family="Georgia", size=12)
                    )
                    lbl.pack(side="left", fill="x", expand=True, padx=10, pady=6)

                    def remove_uid(u=uid):
                        if u in end_user_ids:
                            end_user_ids.remove(u)
                            refresh_list()

                    def edit_uid(u=uid):
                        end_user_entry.delete(0, "end")
                        end_user_entry.insert(0, u)
                        if u in end_user_ids:
                            end_user_ids.remove(u)
                        refresh_list()

                    edit_btn = ctk.CTkButton(
                        item_row,
                        text="Edit",
                        width=60,
                        height=26,
                        corner_radius=6,
                        fg_color=colors["secondary"],
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=edit_uid
                    )
                    edit_btn.pack(side="right", padx=(4, 4))

                    rm_btn = ctk.CTkButton(
                        item_row,
                        text="Remove",
                        width=70,
                        height=26,
                        corner_radius=6,
                        fg_color="#6b6b6b",
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=remove_uid
                    )
                    rm_btn.pack(side="right", padx=(4, 8))

            def add_user_ids():
                raw = end_user_entry.get().strip()
                if not raw:
                    messagebox.showinfo("Info", "Please enter at least one user ID.")
                    return

                ids = [i.strip() for i in raw.split(",") if i.strip()]
                for uid in ids:
                    if uid not in end_user_ids:
                        end_user_ids.append(uid)

                end_user_entry.delete(0, "end")
                refresh_list()

            add_btn.configure(command=add_user_ids)

            prev_data = self.optional_data.get(field, [])
            if isinstance(prev_data, list):
                end_user_ids[:] = prev_data
            refresh_list()

            def build_end_user_json():
                if end_user_ids:
                    return True, end_user_ids
                return True, []

            end_user_entry._get_json = build_end_user_json

            widget = {
                "frame": end_user_frame,
                "_get_json": build_end_user_json
            }
            self.entries[field] = widget

        elif field == "metadata_columns":

            meta_frame = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=10)
            meta_frame.pack(padx=10, pady=(5, 10), fill="x")

            input_row = ctk.CTkFrame(meta_frame, fg_color="transparent")
            input_row.pack(fill="x", padx=10, pady=(6, 6))

            meta_entry = ctk.CTkEntry(
                input_row,
                width=400,
                corner_radius=8,
                placeholder_text="Enter metadata key",
                fg_color=colors["surface"],
                border_color=colors["primary"],
                text_color=colors["primary"],
                font=ctk.CTkFont(family="Georgia", size=13)
            )
            meta_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

            add_btn = ctk.CTkButton(
                input_row,
                text="Add",
                width=80,
                height=32,
                corner_radius=8,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=12)
            )
            add_btn.pack(side="right")

            # ---- List Frame ----
            list_frame = ctk.CTkFrame(meta_frame, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=10, pady=(8, 4))

            metadata_keys = []

            empty_label = ctk.CTkLabel(
                list_frame,
                text="No metadata key added yet.",
                text_color=colors["secondary"],
                font=ctk.CTkFont(family="Georgia", size=12, slant="italic")
            )
            empty_label.pack(pady=10)

            def refresh_list():
                for w in list_frame.winfo_children():
                    w.destroy()

                if not metadata_keys:
                    empty = ctk.CTkLabel(
                        list_frame,
                        text="No metadata key added yet.",
                        text_color=colors["secondary"],
                        font=ctk.CTkFont(family="Georgia", size=12, slant="italic")
                    )
                    empty.pack(pady=10)
                    return

                for key in metadata_keys:
                    row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                    row.pack(fill="x", padx=6, pady=4)

                    lbl = ctk.CTkLabel(
                        row,
                        text=key,
                        text_color=colors["primary"],
                        anchor="w",
                        font=ctk.CTkFont(family="Georgia", size=12)
                    )
                    lbl.pack(side="left", fill="x", expand=True, padx=10, pady=6)

                    def remove_key(k=key):
                        if k in metadata_keys:
                            metadata_keys.remove(k)
                            refresh_list()

                    def edit_key(k=key):
                        meta_entry.delete(0, "end")
                        meta_entry.insert(0, k)
                        if k in metadata_keys:
                            metadata_keys.remove(k)
                        refresh_list()

                    edit_btn = ctk.CTkButton(
                        row, text="Edit", width=60, height=26,
                        corner_radius=6,
                        fg_color=colors["secondary"],
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=edit_key
                    )
                    edit_btn.pack(side="right", padx=(4, 4))

                    rm_btn = ctk.CTkButton(
                        row, text="Remove", width=70, height=26,
                        corner_radius=6,
                        fg_color="#6b6b6b",
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=remove_key
                    )
                    rm_btn.pack(side="right", padx=(4, 8))

            def add_key():
                raw = meta_entry.get().strip()
                if not raw:
                    messagebox.showinfo("Info", "Please enter at least one metadata key.")
                    return

                keys = [k.strip() for k in raw.split(",") if k.strip()]
                for k in keys:
                    if k not in metadata_keys:
                        metadata_keys.append(k)

                meta_entry.delete(0, "end")
                refresh_list()

            add_btn.configure(command=add_key)

            prev = self.optional_data.get(field, [])
            if isinstance(prev, list):
                metadata_keys[:] = prev

            refresh_list()

            def build_meta_json():
                return True, metadata_keys

            widget = {
                "frame": meta_frame,
                "_get_json": build_meta_json
            }

            self.entries[field] = widget

        elif field in ["tags", "languages"]:
            container = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=12)
            container.pack(fill="x", padx=10, pady=(0, 10))

            raw_data = self.optional_data.get(field)
            if not isinstance(raw_data, dict):
                current_data = {"and": [], "or": [], "nor": []}
            else:
                current_data = {"and": [], "or": [], "nor": []}
                for k in ("and", "or", "nor"):
                    items = raw_data.get(k, [])
                    for it in items:
                        if isinstance(it, dict) and "val" in it:
                            current_data[k].append(it)
                        elif isinstance(it, str):
                            current_data[k].append({"val": it, "exists": raw_data.get("exists", "true")})

            input_frame = ctk.CTkFrame(container, fg_color="transparent")
            input_frame.pack(fill="x", padx=10, pady=(8, 6))

            input_var = tk.StringVar()
            input_entry = ctk.CTkEntry(
                input_frame, placeholder_text=f"Enter {field} value",
                textvariable=input_var, width=180, height=32, corner_radius=8,
                font=("Georgia", 12)
            )
            input_entry.pack(side="left", padx=(0, 6))

            option_var = tk.StringVar(value="and")
            option_menu = ctk.CTkOptionMenu(
                input_frame, variable=option_var, values=["and", "or", "nor"],
                width=80, height=32, corner_radius=8,
                fg_color=colors["primary"], button_color=colors["primary"],
                button_hover_color=colors["secondary"], text_color=colors["surface"],
                font=("Georgia", 12)
            )
            option_menu.pack(side="left", padx=(0, 6))

            exists_var = tk.StringVar(value="true")
            exists_menu = ctk.CTkOptionMenu(
                input_frame, variable=exists_var, values=["true", "false"],
                width=80, height=32, corner_radius=8,
                fg_color=colors["primary"], button_color=colors["primary"],
                button_hover_color=colors["secondary"], text_color=colors["surface"],
                font=("Georgia", 12)
            )
            exists_menu.pack(side="left", padx=(0, 6))

            def add_item():
                text = input_var.get().strip()
                if not text:
                    return
                cat = option_var.get()
                item = {"val": text, "exists": exists_var.get()}
                if item not in current_data.get(cat, []):
                    current_data.setdefault(cat, []).append(item)
                input_var.set("")
                refresh_list()

            add_btn = ctk.CTkButton(
                input_frame, text="Add", width=70, height=32,
                fg_color=colors["primary"], hover_color=colors["secondary"],
                text_color=colors["surface"], font=("Georgia", 12),
                command=add_item
            )
            add_btn.pack(side="left", padx=(4, 0))

            # ---------- List Section (BOTTOM) ----------
            list_frame = ctk.CTkFrame(container, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=12, pady=(6, 4))

            def refresh_list():
                for child in list_frame.winfo_children():
                    child.destroy()

                has_any = False
                for k, v_list in current_data.items():
                    for item in list(v_list):
                        has_any = True
                        val = item.get("val")
                        exists_val = item.get("exists", "true")

                        row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                        row.pack(fill="x", padx=6, pady=3)

                        inner = ctk.CTkFrame(row, fg_color="transparent")
                        inner.pack(fill="x", padx=10, pady=4)

                        text_display = f"{k.upper()} → {val}  (exists: {exists_val})"
                        label = ctk.CTkLabel(
                            inner, text=text_display, anchor="w", justify="left",
                            text_color=colors["primary"], font=("Georgia", 12), wraplength=330
                        )
                        label.pack(side="left", fill="x", expand=True, padx=(0, 6))

                        def make_edit(cat, itm):
                            def _edit():
                                input_var.set(itm["val"])
                                option_var.set(cat)
                                exists_var.set(itm.get("exists", "true"))
                                current_data[cat].remove(itm)
                                refresh_list()
                            return _edit

                        def make_remove(cat, itm):
                            def _remove():
                                current_data[cat].remove(itm)
                                refresh_list()
                            return _remove

                        ctk.CTkButton(
                            inner, text="Edit", width=52, height=24,
                            corner_radius=6, fg_color=colors["secondary"],
                            hover_color=colors["primary"], text_color=colors["surface"],
                            font=("Georgia", 11),
                            command=make_edit(k, item)
                        ).pack(side="right", padx=(0, 4))

                        ctk.CTkButton(
                            inner, text="Remove", width=66, height=24,
                            corner_radius=6, fg_color="#6b6b6b", hover_color="#4a4a4a",
                            text_color=colors["surface"], font=("Georgia", 11),
                            command=make_remove(k, item)
                        ).pack(side="right", padx=(4, 4))

                if not has_any:
                    ctk.CTkLabel(
                        list_frame,
                        text=f"No {field} filters added yet.",
                        text_color=colors["secondary"],
                        font=("Georgia", 11, "italic")
                    ).pack(pady=8)

            def _get_json():
                return True, current_data

            refresh_list()
            widget = {
                "input_var": input_var,
                "option_var": option_var,
                "exists_var": exists_var,
                "data": current_data,
                "_get_json": _get_json,
            }
            self.entries[field] = widget
     
        elif field == "ids[issue]":
            issue_frame = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=10)
            issue_frame.pack(padx=10, pady=(5, 10), fill="x")

            input_row = ctk.CTkFrame(issue_frame, fg_color="transparent")
            input_row.pack(fill="x", padx=10, pady=(0, 6))

            issue_entry = ctk.CTkEntry(
                input_row,
                width=400,
                corner_radius=8,
                placeholder_text="Enter issue IDs (comma-separated)",
                fg_color=colors["surface"],
                border_color=colors["primary"],
                text_color=colors["primary"],
                font=ctk.CTkFont(family="Georgia", size=13)
            )
            issue_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

            add_btn = ctk.CTkButton(
                input_row,
                text="Add",
                width=80,
                height=32,
                corner_radius=8,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=12)
            )
            add_btn.pack(side="right")

            # --- Container that fixes the visible height (so CTkScrollableFrame won't expand the page) --- #
            list_container = ctk.CTkFrame(issue_frame, fg_color=colors["background"], corner_radius=8, height=60, width=520)
            list_container.pack(fill="x", padx=10, pady=(8, 4))
            # prevent the container from auto-resizing to children's size
            list_container.pack_propagate(False)

            # --- Scrollable Frame placed inside fixed-height container --- #
            list_frame = ctk.CTkScrollableFrame(
                list_container,
                fg_color="transparent",
                corner_radius=0
            )
            list_frame.pack(fill="both", expand=True, padx=4, pady=4)

            #Loading previous data (persistence)
            selected_data = self.optional_data.get(field, {})
            operator_selected = "or"
            all_issues = selected_data if isinstance(selected_data, dict) else {operator_selected: []}

            # --- Configuration for dynamic sizing ---
            BASE_HEIGHT = 60        # initial visible px
            ROW_HEIGHT = 34         # approx height per row (adjust if necessary)
            MAX_HEIGHT = 180        # maximum visible px before scrolling

            def refresh_list():
                for w in list_frame.winfo_children():
                    w.destroy()

                ids = all_issues.get(operator_selected, [])

                new_height = min(BASE_HEIGHT + len(ids) * ROW_HEIGHT, MAX_HEIGHT)
                list_container.configure(height=new_height)

                if not ids:
                    ctk.CTkLabel(
                        list_frame,
                        text="No issue ID added yet.",
                        text_color=colors["secondary"],
                        font=ctk.CTkFont(family="Georgia", size=11, slant="italic")
                    ).pack(pady=6)
                    return

                for iid in ids:
                    item_row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                    item_row.pack(fill="x", padx=6, pady=4)

                    lbl = ctk.CTkLabel(
                        item_row,
                        text=iid,
                        text_color=colors["primary"],
                        anchor="w",
                        font=ctk.CTkFont(family="Georgia", size=12)
                    )
                    lbl.pack(side="left", fill="x", expand=True, padx=10, pady=6)

                    def remove_iid(i=iid):
                        issue_list = all_issues.get(operator_selected, [])
                        if i in issue_list:
                            issue_list.remove(i)
                            refresh_list()

                    def edit_iid(i=iid):
                        issue_entry.delete(0, "end")
                        issue_entry.insert(0, i)
                        issue_list = all_issues.get(operator_selected, [])
                        if i in issue_list:
                            issue_list.remove(i)
                        refresh_list()

                    edit_btn = ctk.CTkButton(
                        item_row,
                        text="Edit",
                        width=60,
                        height=26,
                        corner_radius=6,
                        fg_color=colors["secondary"],
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=edit_iid
                    )
                    edit_btn.pack(side="right", padx=(4, 4))

                    rm_btn = ctk.CTkButton(
                        item_row,
                        text="Remove",
                        width=70,
                        height=26,
                        corner_radius=6,
                        fg_color="#6b6b6b",
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=remove_iid
                    )
                    rm_btn.pack(side="right", padx=(4, 8))

            def add_issue_ids():
                import re
                raw = issue_entry.get().strip()
                if not raw:
                    messagebox.showinfo("Info", "Please enter at least one issue ID.")
                    return

                if not re.match(r'^[\d,\s]+$', raw):
                    messagebox.showerror("Invalid Input", "Please enter only digits, commas, or spaces.")
                    return

                ids = [i.strip() for i in raw.split(",") if i.strip()]
                current = all_issues.setdefault(operator_selected, [])
                for iid in ids:
                    if iid not in current:
                        current.append(iid)

                issue_entry.delete(0, "end")
                refresh_list()

            add_btn.configure(command=add_issue_ids)
            refresh_list()

            widget = {
                "frame": issue_frame,
                "operator": operator_selected,
                "data": all_issues
            }

            def _get_json():
                """Return backend-ready data for payload."""
                ids = widget["data"].get(widget["operator"], [])
                if not ids:
                    return True, {}
                return True, widget["data"]

            widget["_get_json"] = _get_json
            self.entries[field] = widget

        elif field == "author_emails":
            author_frame = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=10)
            author_frame.pack(padx=10, pady=(5, 10), fill="x")

            input_row = ctk.CTkFrame(author_frame, fg_color="transparent")
            input_row.pack(fill="x", padx=10, pady=(0, 6))

            author_entry = ctk.CTkEntry(
                input_row,
                width=400,
                corner_radius=8,
                placeholder_text="Enter author emails (comma-separated)",
                fg_color=colors["surface"],
                border_color=colors["primary"],
                text_color=colors["primary"],
                font=ctk.CTkFont(family="Georgia", size=13)
            )
            author_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

            add_btn = ctk.CTkButton(
                input_row,
                text="Add",
                width=80,
                height=32,
                corner_radius=8,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=12)
            )
            add_btn.pack(side="right")

            list_frame = ctk.CTkFrame(author_frame, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=10, pady=(8, 4))

            prev_data = self.optional_data.get(field) or self.entries.get(field, {}).get("data")
            author_emails = []
            if isinstance(prev_data, dict):
                author_emails[:] = prev_data.get("or", [])

            empty_label = ctk.CTkLabel(
                list_frame,
                text="No author email added yet.",
                text_color=colors["secondary"],
                font=ctk.CTkFont(family="Georgia", size=12, slant="italic")
            )
            empty_label.pack(pady=10)

            def refresh_list():
                for w in list_frame.winfo_children():
                    w.destroy()

                if not author_emails:
                    ctk.CTkLabel(
                        list_frame,
                        text="No author email added yet.",
                        text_color=colors["secondary"],
                        font=ctk.CTkFont(family="Georgia", size=12, slant="italic")
                    ).pack(pady=10)
                    return

                for email in author_emails:
                    row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                    row.pack(fill="x", padx=6, pady=4)

                    lbl = ctk.CTkLabel(
                        row,
                        text=email,
                        text_color=colors["primary"],
                        anchor="w",
                        font=ctk.CTkFont(family="Georgia", size=12)
                    )
                    lbl.pack(side="left", fill="x", expand=True, padx=10, pady=6)

                    def remove_email(e=email):
                        if e in author_emails:
                            author_emails.remove(e)
                            data = {"or": author_emails}
                            self.optional_data[field] = data
                            self.entries[field]["data"] = data
                            refresh_list()

                    def edit_email(e=email):
                        author_entry.delete(0, "end")
                        author_entry.insert(0, e)
                        if e in author_emails:
                            author_emails.remove(e)
                        data = {"or": author_emails}
                        self.optional_data[field] = data
                        self.entries[field]["data"] = data
                        refresh_list()

                    edit_btn = ctk.CTkButton(
                        row,
                        text="Edit",
                        width=60,
                        height=26,
                        corner_radius=6,
                        fg_color=colors["secondary"],
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=edit_email
                    )
                    edit_btn.pack(side="right", padx=(4, 4))

                    rm_btn = ctk.CTkButton(
                        row,
                        text="Remove",
                        width=70,
                        height=26,
                        corner_radius=6,
                        fg_color="#6b6b6b",
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=remove_email
                    )
                    rm_btn.pack(side="right", padx=(4, 8))

            def add_email():
                raw = author_entry.get().strip()
                if not raw:
                    messagebox.showinfo("Info", "Please enter at least one email.")
                    return

                emails = [e.strip() for e in raw.split(",") if e.strip()]
                invalid = [e for e in emails if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", e)]
                if invalid:
                    messagebox.showwarning("Invalid", f"Invalid email(s): {', '.join(invalid)}")
                    return

                for e in emails:
                    if e not in author_emails:
                        author_emails.append(e)

                data = {"or": author_emails}
                self.optional_data[field] = data
                self.entries[field]["data"] = data

                author_entry.delete(0, "end")
                refresh_list()

            add_btn.configure(command=add_email)
            refresh_list()

            def _get_json():
                if author_emails:
                    return True, {"or": author_emails}
                return True, {}
            
            widget = {
                "frame": author_frame,
                "entry": author_entry,
                "data": {"or": author_emails},
                "_get_json": _get_json
            }
            self.entries[field] = widget

        elif field == "assignee_emails":
            assignee_frame = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=10)
            assignee_frame.pack(padx=10, pady=(5, 10), fill="x")

            input_row = ctk.CTkFrame(assignee_frame, fg_color="transparent")
            input_row.pack(fill="x", padx=10, pady=(0, 6))

            assignee_entry = ctk.CTkEntry(
                input_row,
                width=400,
                corner_radius=8,
                placeholder_text="Enter assignee emails (comma-separated)",
                fg_color=colors["surface"],
                border_color=colors["primary"],
                text_color=colors["primary"],
                font=ctk.CTkFont(family="Georgia", size=13)
            )
            assignee_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

            add_btn = ctk.CTkButton(
                input_row,
                text="Add",
                width=80,
                height=32,
                corner_radius=8,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=12)
            )
            add_btn.pack(side="right")

            list_frame = ctk.CTkFrame(assignee_frame, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=10, pady=(8, 4))

            selected_data = self.optional_data.get(field, {})
            operator_selected = "or"
            all_emails = selected_data if isinstance(selected_data, dict) else {operator_selected: []}

            empty_label = ctk.CTkLabel(
                list_frame,
                text="No assignee email added yet.",
                text_color=colors["secondary"],
                font=ctk.CTkFont(family="Georgia", size=12, slant="italic")
            )
            empty_label.pack(pady=10)

            def refresh_list():
                for w in list_frame.winfo_children():
                    w.destroy()

                emails = all_emails.get(operator_selected, [])
                if not emails:
                    ctk.CTkLabel(
                        list_frame,
                        text="No assignee email added yet.",
                        text_color=colors["secondary"],
                        font=ctk.CTkFont(family="Georgia", size=12, slant="italic")
                    ).pack(pady=10)
                    return

                for email in emails:
                    item_row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                    item_row.pack(fill="x", padx=6, pady=4)

                    lbl = ctk.CTkLabel(
                        item_row,
                        text=email,
                        text_color=colors["primary"],
                        anchor="w",
                        font=ctk.CTkFont(family="Georgia", size=12)
                    )
                    lbl.pack(side="left", fill="x", expand=True, padx=10, pady=6)

                    def remove_email(e=email):
                        emails = all_emails.get(operator_selected, [])
                        if e in emails:
                            emails.remove(e)
                            refresh_list()

                    def edit_email(e=email):
                        assignee_entry.delete(0, "end")
                        assignee_entry.insert(0, e)
                        emails = all_emails.get(operator_selected, [])
                        if e in emails:
                            emails.remove(e)
                        refresh_list()

                    edit_btn = ctk.CTkButton(
                        item_row,
                        text="Edit",
                        width=60,
                        height=26,
                        corner_radius=6,
                        fg_color=colors["secondary"],
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=edit_email
                    )
                    edit_btn.pack(side="right", padx=(4, 4))

                    rm_btn = ctk.CTkButton(
                        item_row,
                        text="Remove",
                        width=70,
                        height=26,
                        corner_radius=6,
                        fg_color="#6b6b6b",
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=remove_email
                    )
                    rm_btn.pack(side="right", padx=(4, 8))

            def add_email():
                raw = assignee_entry.get().strip()
                if not raw:
                    messagebox.showinfo("Info", "Please enter at least one email.")
                    return

                emails = [e.strip() for e in raw.split(",") if e.strip()]
                invalid = [e for e in emails if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", e)]
                if invalid:
                    messagebox.showwarning("Invalid", f"Invalid email(s): {', '.join(invalid)}")
                    return

                current = all_emails.setdefault(operator_selected, [])
                for e in emails:
                    if e not in current:
                        current.append(e)

                assignee_entry.delete(0, "end")
                refresh_list()

            add_btn.configure(command=add_email)
            refresh_list()

            widget = {
                "frame": assignee_frame,
                "operator": operator_selected,
                "data": all_emails
            }

            def _get_json():
                """Return backend-ready data for payload."""
                emails = widget["data"].get(widget["operator"], [])
                if not emails:
                    return True, {}
                return True, widget["data"]
           

            widget["_get_json"] = _get_json
            self.entries[field] = widget

        elif field == "feedback-rating":
            selected_data = self.optional_data.get(field, {})
            operator_selected = "and"
            all_conditions = selected_data if isinstance(selected_data, dict) else {operator_selected: []}

            # outermost frame
            rating_frame = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=10)
            rating_frame.pack(padx=10, pady=(6, 12), fill="x")

            # checkbox to disable feedback rating filtering
            no_filter_var = tk.BooleanVar(value=(not bool(all_conditions)))
            no_filter_chk = ctk.CTkCheckBox(
                rating_frame,
                text="Disable feedback rating",
                variable=no_filter_var,
                onvalue=True,
                offvalue=False,
                corner_radius=6,
                border_width=1,
                checkbox_width=16,
                checkbox_height=16,
                height=22,
                font=ctk.CTkFont(family="Georgia", size=12),
                text_color=colors["primary"],
                fg_color=colors["surface"],
                hover_color=colors["secondary"]
            )
            no_filter_chk.pack(anchor="w", padx=10, pady=(6, 4))

            input_row = ctk.CTkFrame(rating_frame, fg_color="transparent")
            input_row.pack(fill="x", padx=12, pady=(0, 6))

            operator_var = tk.StringVar(value=operator_selected)
            operator_menu = ctk.CTkOptionMenu(
                input_row, values=["and", "or"],
                variable=operator_var,
                width=80, height=32,
                fg_color=colors["primary"],
                button_color=colors["primary"],
                button_hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=12)
            )
            operator_menu.pack(side="left", padx=(0, 6))

            condition_var = tk.StringVar(value="is")
            condition_menu = ctk.CTkOptionMenu(
                input_row, values=["is", "is_not", "is_greater_than", "is_smaller_than"],
                variable=condition_var,
                width=160, height=32,
                fg_color=colors["primary"],
                button_color=colors["primary"],
                button_hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=12)
            )
            condition_menu.pack(side="left", padx=(0, 6))

            value_var = tk.StringVar(value="5")
            value_entry = ctk.CTkEntry(
                input_row, textvariable=value_var,
                width=60, height=32, corner_radius=8,
                font=ctk.CTkFont(family="Georgia", size=12),
                placeholder_text="1–5"
            )
            value_entry.pack(side="left", padx=(0, 6))

            add_btn = ctk.CTkButton(
                input_row, text="+ Add Condition",
                width=140, height=32, corner_radius=8,
                fg_color=colors["primary"], hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=12)
            )
            add_btn.pack(side="left", padx=(8, 0))

            # Conditions List Frame
            condition_list = ctk.CTkFrame(rating_frame, fg_color=colors["background"], corner_radius=8, height=50)
            condition_list.pack(fill="x", padx=12, pady=(8, 4))

            def refresh_conditions():
                for w in condition_list.winfo_children():
                    w.destroy()

                has_any = False
                for op, conds in all_conditions.items():
                    if conds:
                        has_any = True
                        for cond in conds:
                            key = list(cond.keys())[0]
                            val = cond[key]
                            row = ctk.CTkFrame(condition_list, fg_color=colors["surface"], corner_radius=8)
                            row.pack(fill="x", padx=6, pady=3)

                            lbl = ctk.CTkLabel(
                                row, text=f"{op.upper()} {key.replace('_', ' ')} {val}",
                                text_color=colors["primary"], anchor="w",
                                justify="left", font=ctk.CTkFont(family="Georgia", size=12)
                            )
                            lbl.pack(side="left", fill="x", expand=True, padx=8)

                            rm_btn = ctk.CTkButton(
                                row, text="Remove", width=70, height=26,
                                corner_radius=6,
                                fg_color="#6b6b6b",          # changed from colors["secondary"]
                                hover_color="#4a4a4a",       # subtle darker hover tone
                                text_color=colors["surface"],
                                font=ctk.CTkFont(family="Georgia", size=11),
                                command=lambda op=op, cond=cond: remove_condition(op, cond)
                            )

                            rm_btn.pack(side="right", padx=(4, 6))

                if not has_any:
                    ctk.CTkLabel(
                        condition_list,
                        text="No feedback condition added yet.",
                        text_color=colors["secondary"],
                        font=ctk.CTkFont(family="Georgia", size=12, slant="italic")
                    ).pack(pady=8)

            def remove_condition(op, cond):
                if cond in all_conditions.get(op, []):
                    all_conditions[op].remove(cond)
                refresh_conditions()

            def add_condition():
                if no_filter_var.get():
                    messagebox.showinfo("Info", "Uncheck 'Disable feedback rating' to add conditions.")
                    return

                op = operator_var.get()
                cond = condition_var.get()
                val = value_var.get().strip()

                if not val.isdigit() or not (1 <= int(val) <= 5):
                    messagebox.showwarning("Invalid Value", "Rating must be a number between 1 and 5.")
                    return

                all_conditions.setdefault(op, []).append({cond: val})
                refresh_conditions()

            add_btn.configure(command=add_condition)

            refresh_conditions()

            widget = {
                "frame": rating_frame,
                "no_filter_var": no_filter_var,
                "operator_var": operator_var,
                "condition_var": condition_var,
                "value_var": value_var,
                "data": all_conditions
            }

            def _get_json():
                if widget["no_filter_var"].get() or not any(widget["data"].values()):
                    return True, {}
                return True, widget["data"]

            widget["_get_json"] = _get_json
            self.entries[field] = widget

        elif field == "custom_fields":
            cf_frame = ctk.CTkFrame(body, fg_color=colors["surface"], corner_radius=12)
            cf_frame.pack(padx=10, pady=(0, 8), anchor="w", fill="x")


            saved_cf = self.optional_data.get("custom_fields", {})
            split_var = tk.BooleanVar(
                master=self.frame,
                value=bool(saved_cf.get("split", False))
            )


            split_row = ctk.CTkFrame(cf_frame, fg_color="transparent")
            split_row.pack(fill="x", padx=10, pady=(10, 4))

            split_checkbox = ctk.CTkCheckBox(
                split_row,
                text="Export custom fields in separate columns",
                variable=split_var,
                corner_radius=6,
                border_width=1,
                checkbox_width=16,
                checkbox_height=16,
                text_color=colors["primary"],
                font=ctk.CTkFont(family="Georgia", size=12)
            )
            split_checkbox.pack(anchor="w")

            column_keys = list(saved_cf.get("columns", []))

            columns_frame = ctk.CTkFrame(cf_frame, fg_color=colors["background"], corner_radius=8)


            def toggle_columns():
                if split_var.get():
                    columns_frame.pack(fill="x", padx=12, pady=(6, 6))
                    refresh_columns()
                else:
                    columns_frame.pack_forget()


            split_checkbox.configure(command=toggle_columns)
            # Restore columns UI if previously enabled
    
            if split_var.get():
                self.master.after(50, toggle_columns)

            header_row = ctk.CTkFrame(columns_frame, fg_color="transparent")
            header_row.pack(fill="x", padx=8, pady=(6, 4))

            ctk.CTkLabel(
                header_row,
                text="Custom Field Columns",
                text_color=colors["primary"],
                font=ctk.CTkFont(family="Georgia", size=13, weight="bold")
            ).pack(side="left")

            ctk.CTkButton(
                header_row,
                text="+ Add",
                width=70,
                height=26,
                corner_radius=6,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=ctk.CTkFont(family="Georgia", size=11),
                command=lambda: open_column_popup()
            ).pack(side="right")

            columns_list = ctk.CTkFrame(columns_frame, fg_color="transparent")
            columns_list.pack(fill="x", padx=4, pady=(0, 6))


            def refresh_columns():
                for w in columns_list.winfo_children():
                    w.destroy()

                if not column_keys:
                    ctk.CTkLabel(
                        columns_list,
                        text="No custom field columns added yet.",
                        text_color=colors["secondary"],
                        font=ctk.CTkFont(family="Georgia", size=11, slant="italic")
                    ).pack(pady=6)
                    return

                for key in list(column_keys):
                    row = ctk.CTkFrame(columns_list, fg_color=colors["surface"], corner_radius=8)
                    row.pack(fill="x", padx=6, pady=3)

                    inner = ctk.CTkFrame(row, fg_color="transparent")
                    inner.pack(fill="x", padx=10, pady=4)

                    ctk.CTkLabel(
                        inner,
                        text=key,
                        text_color=colors["primary"],
                        font=ctk.CTkFont(family="Georgia", size=12),
                        anchor="w"
                    ).pack(side="left", fill="x", expand=True)

                    def make_edit(k):
                        return lambda: open_column_popup(k)

                    def make_remove(k):
                        return lambda: (column_keys.remove(k), refresh_columns())

                    ctk.CTkButton(
                        inner,
                        text="Edit",
                        width=52,
                        height=24,
                        corner_radius=6,
                        fg_color=colors["secondary"],
                        hover_color=colors["primary"],
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=make_edit(key)
                    ).pack(side="right", padx=(0, 4))

                    ctk.CTkButton(
                        inner,
                        text="Remove",
                        width=66,
                        height=24,
                        corner_radius=6,
                        fg_color="#6b6b6b",
                        hover_color="#4a4a4a",
                        text_color=colors["surface"],
                        font=ctk.CTkFont(family="Georgia", size=11),
                        command=make_remove(key)
                    ).pack(side="right", padx=(4, 4))

            def open_column_popup(edit_key=None):
                top = ctk.CTkToplevel(cf_frame)
                top.title("Custom Field Column")
                top.geometry("420x220")
                top.resizable(False, False)

                ctk.CTkLabel(
                    top,
                    text="Edit Column" if edit_key else "Add Column",
                    font=ctk.CTkFont(family="Georgia", size=14, weight="bold")
                ).pack(pady=(14, 10))

                key_var = tk.StringVar(value=edit_key or "")

                ctk.CTkLabel(
                    top,
                    text="Custom field key",
                    font=ctk.CTkFont(family="Georgia", size=12)
                ).pack(anchor="w", padx=24)

                entry = ctk.CTkEntry(
                    top,
                    textvariable=key_var,
                    width=340,
                    font=ctk.CTkFont(family="Georgia", size=12)
                )
                entry.pack(padx=24, pady=(4, 12))

                def save():
                    k = key_var.get().strip()
                    if not k:
                        messagebox.showwarning("Invalid", "Key cannot be empty.")
                        return

                    if edit_key and edit_key in column_keys:
                        column_keys.remove(edit_key)

                    if k not in column_keys:
                        column_keys.append(k)

                    refresh_columns()
                    top.destroy()

                ctk.CTkButton(
                    top,
                    text="Save",
                    command=save,
                    fg_color=colors["primary"],
                    hover_color=colors["secondary"],
                    text_color=colors["surface"],
                    corner_radius=8,
                    width=120,
                    font=ctk.CTkFont(family="Georgia", size=12)
                ).pack(pady=16)

                top.grab_set()

            raw_cf = self.optional_data.get(field, {})

            if isinstance(raw_cf, dict):
                json_data = copy.deepcopy(raw_cf.get("filters", {}))
                split_var.set(bool(raw_cf.get("split", False)))
                column_keys[:] = list(copy.deepcopy(raw_cf.get("columns", [])))
            else:
                json_data = {}

            if not isinstance(json_data, dict):
                json_data = {}

            types = ["checkbox", "singleline", "multiline", "number", "date", "dropdown"]
            conditions = ["and", "or"]

            op_map = {
                "checkbox": ["true", "false"],
                "singleline": ["is_set", "contains", "does_not_contain"],
                "multiline": ["is_set", "contains", "does_not_contain"],
                "number": ["is_set", "is", "is_not", "is_greater_than", "is_smaller_than"],
                "date": ["is_set", "is", "is_not", "is_before", "is_after"],
                "dropdown": ["is_set", "is", "is_not", "is_one_of", "is_none_of"]
            }

            # ---------- List display ----------
            list_frame = ctk.CTkFrame(cf_frame, fg_color=colors["background"], corner_radius=8)
            list_frame.pack(fill="x", padx=12, pady=(2, 2))

            def refresh_list():
                for w in list_frame.winfo_children():
                    w.destroy()

                has_any = False
                for ftype, conds in json_data.items():
                    for cond, keys in conds.items():
                        for key, ops in keys.items():
                            for op, val in ops.items():
                                has_any = True

                                row = ctk.CTkFrame(list_frame, fg_color=colors["surface"], corner_radius=8)
                                row.pack(fill="x", padx=6, pady=3)

                                inner = ctk.CTkFrame(row, fg_color="transparent")
                                inner.pack(fill="x", padx=10, pady=4)

                                display_text = f"{cond.upper()} → ({ftype}, key: {key}, op: {op}, value: {val})"
                                if len(display_text) > 90:
                                    display_text = display_text[:90] + "..."

                                label = ctk.CTkLabel(
                                    inner,
                                    text=display_text,
                                    anchor="w",
                                    justify="left",
                                    text_color=colors["primary"],
                                    font=ctk.CTkFont(family="Georgia", size=12),
                                    wraplength=330
                                )
                                label.pack(side="left", fill="x", expand=True, padx=(0, 6))

                                def make_edit(ftype, cond, key, op, val):
                                    def _edit():
                                        open_popup(ftype, cond, key, op, val, edit_mode=True)
                                    return _edit

                                def make_remove(ftype, cond, key, op):
                                    def _remove():
                                        del json_data[ftype][cond][key][op]
                                        if not json_data[ftype][cond][key]:
                                            del json_data[ftype][cond][key]
                                        if not json_data[ftype][cond]:
                                            del json_data[ftype][cond]
                                        if not json_data[ftype]:
                                            del json_data[ftype]
                                        refresh_list()
                                    return _remove

                                ctk.CTkButton(
                                    inner, text="Edit", width=52, height=24,
                                    corner_radius=6, fg_color=colors["secondary"],
                                    hover_color=colors["primary"], text_color=colors["surface"],
                                    font=ctk.CTkFont(family="Georgia", size=11),
                                    command=make_edit(ftype, cond, key, op, val)
                                ).pack(side="right", padx=(0, 4))

                                ctk.CTkButton(
                                    inner, text="Remove", width=66, height=24,
                                    corner_radius=6, fg_color="#6b6b6b", hover_color="#4a4a4a",
                                    text_color=colors["surface"],
                                    font=ctk.CTkFont(family="Georgia", size=11),
                                    command=make_remove(ftype, cond, key, op)
                                ).pack(side="right", padx=(4, 4))

                if not has_any:
                    ctk.CTkLabel(
                        list_frame,
                        text="No custom fields added yet.",
                        text_color=colors["secondary"],
                        font=ctk.CTkFont(family="Georgia", size=11, slant="italic")
                    ).pack(pady=8)

            def open_popup(ftype=None, cond=None, key=None, op=None, val=None, edit_mode=False):
                top = ctk.CTkToplevel(body)
                top.title("Edit Custom Field" if edit_mode else "Add Custom Field")
                top.geometry("450x520")
                top.resizable(False, False)

                ctk.CTkLabel(
                    top,
                    text="Edit Custom Field" if edit_mode else "Add a New Custom Field",
                    font=ctk.CTkFont(family="Georgia", size=14, weight="bold")
                ).pack(pady=(10, 5))

                # Field type
                ctk.CTkLabel(top, text="Select Field Type:", font=("Georgia", 12)).pack(anchor="w", padx=20, pady=(10, 3))
                type_var = tk.StringVar(value=ftype or types[0])
                type_menu = ctk.CTkOptionMenu(top, values=types, variable=type_var, font=("Georgia", 12))
                type_menu.pack(anchor="w", padx=20)

                # Condition
                ctk.CTkLabel(top, text="Select Condition (AND / OR):", font=("Georgia", 12)).pack(anchor="w", padx=20, pady=(10, 3))
                cond_var = tk.StringVar(value=cond or conditions[0])
                cond_menu = ctk.CTkOptionMenu(top, values=conditions, variable=cond_var, font=("Georgia", 12))
                cond_menu.pack(anchor="w", padx=20)

                # Key
                key_var = tk.StringVar(value=key or "")
                ctk.CTkLabel(top, text="Custom Field Key (from dashboard):", font=("Georgia", 12)).pack(anchor="w", padx=20, pady=(10, 3))
                key_entry = ctk.CTkEntry(top, textvariable=key_var, placeholder_text="e.g. delivery_date", font=("Georgia", 12), width=380)
                key_entry.pack(anchor="w", padx=20, fill="x")

                # Operator
                ctk.CTkLabel(top, text="Select Operator:", font=("Georgia", 12)).pack(anchor="w", padx=20, pady=(10, 3))
                op_var = tk.StringVar(value=op or op_map[types[0]][0])
                op_menu = ctk.CTkOptionMenu(top, values=op_map[type_var.get()], variable=op_var, font=("Georgia", 12))
                op_menu.pack(anchor="w", padx=20)

                def update_ops(*_):
                    op_menu.configure(values=op_map[type_var.get()])
                    op_var.set(op_map[type_var.get()][0])
                type_var.trace_add("write", update_ops)

                # Value
                ctk.CTkLabel(top, text="Enter Value:", font=("Georgia", 12)).pack(anchor="w", padx=20, pady=(10, 3))
                value_var = tk.StringVar(value=str(val) if val is not None else "")
                ctk.CTkEntry(top, textvariable=value_var, placeholder_text="e.g. 5, true, INR", font=("Georgia", 12)).pack(anchor="w", padx=20, fill="x")

                # Save Field
                
                def save_field():
                    ctype = type_var.get()
                    condx = cond_var.get()
                    keyx = key_var.get().strip()
                    opx = op_var.get()
                    valx = value_var.get().strip()

                    if not keyx:
                        messagebox.showwarning("Missing Data", "Please provide a valid key name.")
                        return

                    # --- Convert value to correct type ---in
                    if valx.lower() == "true":
                        val_parsed = True
                    elif valx.lower() == "false":
                        val_parsed = False
                    elif valx.isdigit():
                        val_parsed = int(valx)
                    else:
                        val_parsed = valx.strip()

                    #  Operators that require ARRAY values
                    ARRAY_OPS = {"contains", "does_not_contain", "is_one_of", "is_none_of"}

                    if opx in ARRAY_OPS:
                        # Always wrap into list (preserve case)
                        if not isinstance(val_parsed, list):
                            val_parsed = [val_parsed]

                    # If editing, remove old entry first 
                    if edit_mode and ftype and cond and key and op:
                        try:
                            del json_data[ftype][cond][key][op]
                           
                            if not json_data[ftype][cond][key]:
                                del json_data[ftype][cond][key]
                            if not json_data[ftype][cond]:
                                del json_data[ftype][cond]
                            if not json_data[ftype]:
                                del json_data[ftype]
                        except KeyError:
                            pass  # Safe fallback if it was already gone
                        # Now set new/edited value
                    json_data.setdefault(ctype, {}).setdefault(condx, {}).setdefault(keyx, {})[opx] = val_parsed

                    top.destroy()
                    refresh_list()

                ctk.CTkButton(
                    top,
                    text="Save Field",
                    command=save_field,
                    corner_radius=10,
                    font=("Georgia", 12)
                ).pack(pady=20)

                top.grab_set()
                body.wait_window(top)

            ctk.CTkButton(
                cf_frame,
                text="+ Add Custom Field",
                command=lambda: open_popup(),
                corner_radius=10,
                fg_color=colors["primary"],
                hover_color=colors["secondary"],
                text_color=colors["surface"],
                font=("Georgia", 12)
            ).pack(pady=(4, 10), padx=10, anchor="w")

    

            def build_custom_fields_json():
                return True, {
                    "filters": copy.deepcopy(json_data),
                    "split": bool(split_var.get()),
                    "columns": list(column_keys)
                }

            widget = {
                "frame": cf_frame,
                "data": json_data,
            }
            widget["_get_json"] = build_custom_fields_json
            self.entries[field] = widget

            refresh_list()

        else:
            widget = ctk.CTkEntry(
                body, width=250, height=40, corner_radius=8,
                font=ctk.CTkFont(family="Georgia", size=14),
                fg_color=colors["surface"], border_color=colors["primary"],
                text_color=colors["primary"]
            )
            if field in self.optional_data:
                widget.insert(0, self.optional_data[field])


        def toggle_body(_):
            if body.winfo_ismapped():
                body.pack_forget()
            else:
                body.pack(fill="x", pady=(0,6))
        header.bind("<Button-1>", toggle_body)
        header_label.bind("<Button-1>", toggle_body)


    def get_value(self, widget):
        if hasattr(widget, "get") and callable(widget.get):
            try:
                val = widget.get()
                if isinstance(val, str):
                    return val.strip()
                return val
            except Exception:
                return None
        return None

    def go_previous(self):
        new_optional_data = {}
        for f, w in self.entries.items():
            if isinstance(w, dict) and "_get_json" in w:
                try:
                    ok, val = w["_get_json"]()
                    if ok:
                        new_optional_data[f] = val
                except Exception as e:
                    print(f"Error extracting {f}:", e)
            else:
                val = self.get_value(w)
                if val not in (None, "", [], {}):
                    new_optional_data[f] = val

        print("Persisted optional data:", new_optional_data)

        for child in self.frame.winfo_children():
            try:
                child.destroy()
            except:
                pass

        self.entries.clear()
        self.frame.destroy()

        from mandatory_page import MandatoryPage
        MandatoryPage(
            self.master,
            form_data=self.form_data,
            optional_data=new_optional_data
        )

    def _export_worker(self, payload, save_path, save_as_json=False):
        """Background thread: download export file and update UI via marquee."""
        tmp_path = None
        try:
            export_url = f"{API_BASE_URL}/export/"

            # create temp file to stream into (avoid partial writes to final path)
            fd, tmp_path = tempfile.mkstemp(suffix=".csv", prefix="download_")
            os.close(fd)

            with requests.post(export_url, json=payload, stream=True, timeout=None) as resp:
                if resp.status_code != 200:
                    try:
                        txt = resp.text
                    except Exception:
                        txt = str(resp.status_code)
                    self.frame.after(0, lambda: messagebox.showerror("Error", f"Export API failed: {txt}"))
                    return

                with open(tmp_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
                        # no percent updates — marquee shows activity

            # download complete. If user wanted JSON, convert; else move to final path
            if save_as_json:
                # Convert CSV → JSON streaming
                self.frame.after(0, lambda: self._progress_label.configure(text="Converting CSV → JSON..."))
                written = 0
                with open(tmp_path, "r", encoding="utf-8", newline="") as csvfile, open(save_path, "w", encoding="utf-8", newline="") as jsonfile:
                    reader = _csv.DictReader(csvfile)
                    jsonfile.write("[\n")
                    first = True
                    for row in reader:
                        if not first:
                            jsonfile.write(",\n")
                        json.dump(row, jsonfile, ensure_ascii=False)
                        first = False
                        written += 1
                    jsonfile.write("\n]\n")
                try:
                    os.remove(tmp_path)
                    tmp_path = None
                except Exception:
                    pass
            else:
                # move file into user chosen save_path
                shutil.move(tmp_path, save_path)
                tmp_path = None

            # stop marquee and show completion
            self.frame.after(0, lambda: self._stop_marquee("Download complete"))
            self.frame.after(600, lambda: messagebox.showinfo("Export Complete", f"Export saved to:\n{save_path}"))

        except requests.exceptions.RequestException as re:
            print("Network error during export:", re)
            self.frame.after(0, lambda: messagebox.showerror("Error", f"Network error during export:\n{re}"))
        except Exception as e:
            print("Export/convert error:", e)
            self.frame.after(0, lambda: messagebox.showerror("Error", f"Export error:\n{e}"))
        finally:
            # cleanup temp if left
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

            # restore UI & re-enable buttons
            try:
                self.frame.after(0, lambda: self.submit_btn.configure(state="normal"))
                self.frame.after(0, lambda: self.back_btn.configure(state="normal"))
            except Exception:
                pass

    def _start_downloading_animation(self):
        """Show a simple animated 'Downloading...' indicator."""
        try:
            self._progress_frame.pack(fill="x", pady=(10, 0))
        except Exception:
            pass
        
        self._download_anim_running = True
        self._download_anim_dots = 0
    
        def animate():
            if not getattr(self, "_download_anim_running", False):
                return
            dots = "." * (self._download_anim_dots % 4)
            self._progress_label.configure(text=f"Downloading{dots}")
            self._download_anim_dots += 1
            self.frame.after(400, animate)
    
        animate()

    def _stop_downloading_animation(self, final_text="Download complete"):
        """Stop animation, show final text, and hide frame after delay."""
        self._download_anim_running = False
        self._progress_label.configure(text=final_text)

        def hide():
            try:
                self._progress_frame.pack_forget()
            except:
                pass

        self.frame.after(1200, hide)

    def _start_marquee(self, text="Downloading…"):
        """Show the indeterminate marquee animation with progress polling."""
        try:
            self._progress_frame.pack(fill="x", pady=(0, 10))
        except:
            pass

        try:
            self._progress_label.configure(text=text)
        except:
            pass

        # Setup animation state
        self._marquee_running = True
        # initial pos left of track
        try:
            self._marquee_pos = -self._marquee_bar.winfo_reqwidth()
        except:
            self._marquee_pos = -100

        # Ensure geometry is measured
        self.frame.update_idletasks()
        track_width = self._marquee_track.winfo_width()
        bar_width = self._marquee_bar.winfo_reqwidth()
        if not track_width or track_width < 10:
            track_width = max(400, int(self.master.winfo_width()) - 60)

        self._marquee_end = track_width
        self._marquee_speed = 8  # pixels per frame (tweakable)

        def animate():
            if not getattr(self, "_marquee_running", False):
                return

            try:
                self._marquee_pos += self._marquee_speed
                if self._marquee_pos > self._marquee_end:
                    self._marquee_pos = -bar_width - 20
                self._marquee_bar.place_configure(x=int(self._marquee_pos))
            except Exception:
                pass

            self.frame.after(30, animate)  # ~33 FPS

        # Poll progress every 500ms to show issue count and status
        def poll_progress():
            if not getattr(self, "_marquee_running", False):
                return
            
            try:
                response = requests.get(f"{API_BASE_URL}/export/progress", timeout=5)
                if response.status_code == 200:
                    progress = response.json()
                    fetched = progress.get("fetched", 0)
                    total = progress.get("total", 0)
                    status = progress.get("status", "idle")
                    wait_until = progress.get("wait_until")
                    
                    # Handle different statuses
                    if status == "rate-limited" and wait_until:
                        # Calculate remaining wait time
                        import time as time_module
                        now = time_module.time()
                        remaining_wait = max(0, wait_until - now)
                        
                        if remaining_wait > 0:
                            # Show waiting message
                            self._progress_label.configure(
                                text=f"Rate limit reached. Waiting {int(remaining_wait)}s before resuming..."
                            )
                            # Poll less frequently during wait (every 2 seconds instead of 500ms)
                            self.frame.after(2000, poll_progress)
                            return
                        else:
                            # Wait is over, resume normal polling
                            status = "fetching"
                    
                    # Show fetching progress with total and percentage
                    if status == "fetching" and fetched > 0:
                        if total > 0:
                            percentage = int((fetched / total) * 100)
                            self._progress_label.configure(
                                text=f"Downloading… ({fetched:,} / {total:,} issues) {percentage}%"
                            )
                        else:
                            self._progress_label.configure(
                                text=f"Downloading… ({fetched:,} issues)"
                            )
                    
            except Exception as e:
                print(f"Progress poll error: {e}")
            
            # Normal polling interval when fetching (500ms)
            self.frame.after(500, poll_progress)

        # start animations
        animate()
        poll_progress()

        animate()

    def _stop_marquee(self, final_text="Download complete"):
        """Stop marquee animation & hide after a brief delay."""
        try:
            self._marquee_running = False
        except Exception:
            pass

        try:
            self._progress_label.configure(text=final_text)
        except Exception:
            pass

        def hide():
            try:
                self._progress_frame.pack_forget()
            except Exception:
                pass

        self.frame.after(1200, hide)

    def submit(self):
        """Build payload, ask Save-As dialog, start marquee, launch worker."""
        self.is_exporting = True  # Set flag to indicate export in progress
        data_to_send = {}
        json_fields = [
            "tags", "languages", "custom_fields",
            "author_emails", "assignee_emails", "feedback-rating"
        ]
        for f, w in self.entries.items():
            val = self.get_value(w)
            if isinstance(w, tk.Text):
                if isinstance(val, str):
                    val = val.strip()
                    if val:
                        try:
                            val = json.loads(val)
                        except json.JSONDecodeError:
                            messagebox.showerror(
                                "Invalid Input",
                                f"Field '{f}' contains invalid JSON. Please fix it before submitting."
                            )
                            return
                    else:
                        val = {}
                else:
                    val = {}
            elif isinstance(w, dict):
                if "_get_json" in w:
                    try:
                        ok, val = w["_get_json"]()
                        if not ok:
                            val = {}
                    except Exception as e:
                        print(f"Error parsing JSON field {f}: {e}")
                        val = {}
                else:
                    selected_opts = []
                    for k, v in w.items():
                        try:
                            if hasattr(v, "get"):
                                if v.get():
                                    selected_opts.append(k)
                            elif hasattr(v, "_variable") and v._variable.get():
                                selected_opts.append(k)
                        except Exception as e:
                            print(f"Warning: could not read state for {k}: {e}")
                    val = selected_opts if selected_opts else {}
            else:
                if isinstance(val, str):
                    val = val.strip()
                    if f in json_fields and val:
                        val = [v.strip() for v in val.split(",") if v.strip()]
                elif isinstance(val, dict):
                    pass
                if val in ("", "Select", "Select...", "Select app(s)...", "Select queues..."):
                    val = None
            data_to_send[f] = val

        for jf in json_fields:
            if jf not in data_to_send or not data_to_send[jf]:
                data_to_send[jf] = {}

        if "state" in data_to_send:
            val = data_to_send["state"]
            if isinstance(val, list):
                data_to_send["state"] = ",".join(val)
        if "app-ids" in data_to_send:
            val = data_to_send["app-ids"]
            if isinstance(val, str):
                val = [val]
            elif not isinstance(val, list):
                val = []
            data_to_send["app-ids"] = val
        if "ids[issue]" in data_to_send:
            val = data_to_send["ids[issue]"]
            if isinstance(val, dict) and "or" in val:
                data_to_send["ids"] = val["or"]
            elif isinstance(val, list):
                data_to_send["ids"] = val
            data_to_send.pop("ids[issue]", None)

        if "queue_ids" in data_to_send:
            val = data_to_send.pop("queue_ids", None)
            if val:
                if isinstance(val, list):
                    data_to_send["queue_ids"] = [str(v) for v in val]
                else:
                    data_to_send["queue_ids"] = [str(val)]

       

        data_to_send = {k: v for k, v in data_to_send.items() if v not in (None, {}, [], "")}

        print(":receipt: Final payload before sending:")
        print(json.dumps(data_to_send, indent=2))

        #  Prompt Save As on main thread BEFORE starting download
        domain = self.form_data.get("domain", "export")
        start_time = self.form_data.get("start_datetime", "").replace(" ", "_").replace(":", "-")
        end_time = self.form_data.get("end_datetime", "").replace(" ", "_").replace(":", "-")
        default_name = f"{domain}_{start_time}_{end_time}.csv"
        
        save_path = filedialog.asksaveasfilename(
            title="Save exported file",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not save_path:
            messagebox.showinfo("Cancelled", "Export cancelled by user.")
            return

        # Determine whether user wants JSON output (based on filename extension)
        _save_ext = os.path.splitext(save_path)[1].lower()
        save_as_json = _save_ext == ".json"

        # disable buttons and start marquee
        try:
            self.submit_btn.configure(state="disabled")
            self.back_btn.configure(state="disabled")
        except Exception:
            pass

        # start marquee animation
        try:
            self._start_marquee("Preparing download…")
        except Exception:
            pass


        raw_optional = {}
        
        for f, w in self.entries.items():
            if isinstance(w, dict) and "_get_json" in w:
                try:
                    ok, val = w["_get_json"]()
                    if ok:
                        raw_optional[f] = val
                except:
                    pass
            else:
                raw_optional[f] = self.get_value(w)
        
        print("RAW OPTIONAL PAYLOAD:")
        print(json.dumps(raw_optional, indent=2))
        
        try:
            opt_res = requests.post(
                f"{API_BASE_URL}/optional/",
                json=raw_optional,
                timeout=10
            )
            print("OPTIONAL SAVE STATUS:", opt_res.status_code, opt_res.text)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send filters to backend: {e}")
            return
        


        # start worker
        worker = threading.Thread(target=self._export_worker, args=(data_to_send, save_path, save_as_json), daemon=True)
        worker.start()
        self.is_exporting = False  # Reset flag after starting export

    def _on_resize(self, event):
        try:
            if event.width > 200:
                left_width = int(event.width * 0.35)
                right_width = int(event.width * 0.65)
                children = self.frame.winfo_children()
                if len(children) >= 2:
                    children[0].configure(width=left_width)
                    children[1].configure(width=right_width)
        except Exception as e:
            print(f"Resize error: {e}")
    
    def get_limited_name(self, max_len=25):
        """Custom dialog to get preference name with character limit."""
        top = tk.Toplevel(self.master)
        top.title("Save Preference")
        top.geometry("300x120")
        top.resizable(False, False)
        
        tk.Label(top, text="Enter preference name (max 25 chars):").pack(pady=10)
        
        var = tk.StringVar()
        entry = tk.Entry(top, textvariable=var, width=30)
        entry.pack(pady=5)
        
        def limit_input(*args):
            value = var.get()
            if len(value) > max_len:
                var.set(value[:max_len])
        
        var.trace_add("write", limit_input)
        
        result = None
        def on_ok():
            nonlocal result
            result = var.get().strip()
            top.destroy()
        
        def on_cancel():
            nonlocal result
            result = None
            top.destroy()
        
        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="OK", command=on_ok).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)
        
        top.wait_window()
        return result
    
    def save_current_filters(self):

        name = self.get_limited_name()


        if not name:
            return

        data = {}

        for field, widget in self.entries.items():

            if isinstance(widget, dict) and "_get_json" in widget:
                ok, val = widget["_get_json"]()
                if ok:
                    data[field] = val

            else:
                val = self.get_value(widget)

                if val not in (None, "", [], {}):
                    data[field] = val

        save_preferences(name, data)

        messagebox.showinfo("Saved", "Preference saved successfully!")

        self.render_saved_preferences()

    def render_saved_preferences(self):

        # clear old UI
        for w in self.saved_filters_frame.winfo_children():
            w.destroy()

        prefs = load_preferences()

        if not prefs:
            empty_label = ctk.CTkLabel(
                self.saved_filters_frame,
                text="No saved filters",
                text_color="gray",
                font=ctk.CTkFont(family="Georgia", size=13)
            )
            empty_label.pack(pady=40, padx=20)
            # Force update to ensure label is visible
            self.saved_filters_frame.update_idletasks()
            return

        for name, data in prefs.items():

            row = ctk.CTkFrame(
                self.saved_filters_frame,
                fg_color="#F9FAFB",
                corner_radius=10,
                height=60
            )
            row.pack(fill="x", padx=10, pady=5)
            
            # Filter name
            label = ctk.CTkLabel(
                row,
                text=name,
                anchor="w",
                justify="left",
                wraplength=220
            )
            label.pack(side="left", fill="x", expand=True)

            # ✅ APPLY BUTTON (icon style)
            apply_btn = ctk.CTkButton(
                row,
                text="✔",
                width=28,
                height=28,
                corner_radius=8,
                fg_color="#22C55E",
                hover_color="#16A34A"
            )
            apply_btn.pack(side="right", padx=5)

            apply_btn.configure(
                command=lambda d=data: self.apply_saved_filter(d)
            )

            # ❌ DELETE BUTTON
            delete_btn = ctk.CTkButton(
                row,
                text="✕",
                width=28,
                height=28,
                corner_radius=8,
                fg_color="#989292",
                hover_color="#898584"
            )
            delete_btn.pack(side="right")

            delete_btn.configure(
                command=lambda n=name: self.delete_saved_filter(n)
            )



    def load_pref_into_form(self, data):

        for field, value in data.items():

            widget = self.entries.get(field)

            if not widget:
                continue

            try:

                # OPTION MENU / SINGLE VALUE WIDGET
                if isinstance(widget, dict) and "widget" in widget:
                    widget["widget"].set(value)

                # LIST TYPE DATA
                elif isinstance(widget, dict) and "data" in widget:

                    current_data = widget["data"]

                    if isinstance(current_data, list):
                    
                        current_data.clear()

                        # 🔥 FIX: handle scalar values properly
                        if isinstance(value, list):
                            current_data.extend(value)

                        elif isinstance(value, (int, float)):
                            current_data.append(value)

                        elif isinstance(value, str):
                        
                            # 🔥 handle string list like "[12345]"
                            if value.startswith("[") and value.endswith("]"):
                                try:
                                    parsed = value.strip("[]")
                                    if parsed.isdigit():
                                        current_data.append(int(parsed))
                                    else:
                                        current_data.append(parsed)
                                except:
                                    current_data.append(value)
                            else:
                                current_data.append(value)

                        else:
                            current_data.append(value)

                    # DICT TYPE DATA (like notes / feedback-comment)
                    elif isinstance(current_data, dict):

                        current_data.clear()

                        if isinstance(value, dict):
                            current_data.update(value)

                # SPECIAL CASES
                elif "vars" in widget:
                    for k, v in widget["vars"].items():
                        v.set(k in value)

            except Exception as e:
                print("Load filter error:", e)

    def delete_pref(self, name):

        delete_preference(name)

        self.render_saved_preferences()


    def toggle_saved_filters(self):
        self.master.update_idletasks()

        if self.saved_filters_frame.winfo_ismapped():
            self.saved_filters_frame.place_forget()
        else:
            # Render preferences first to populate the dropdown
            self.render_saved_preferences()
            self.saved_filters_frame.update_idletasks()
            
            # Get button position (relative inside parent)
            btn_y = self.saved_filters_btn.winfo_y()
            btn_height = self.saved_filters_btn.winfo_height()

            # Place dropdown aligned to RIGHT side of parent
            self.saved_filters_frame.place(
                relx=0.98,  # slight margin from right edge
                y=btn_y + btn_height + 5,
                anchor="ne"  # ⭐ THIS IS THE KEY FIX
            )

            self.saved_filters_frame.lift()  # bring to front




    def apply_saved_filter(self, data):
        try:
            normalized = {}

            for k, v in data.items():

                if k == "custom_fields":
                    normalized[k] = self._fix_custom_fields(v)

                elif isinstance(v, dict):
                    normalized[k] = v
                elif isinstance(v, list):
                    normalized[k] = v
                elif isinstance(v, (int, str)):
                    normalized[k] = [v]
                else:
                    normalized[k] = []

            # 🔥 EXTRA SAFETY
            if not isinstance(normalized.get("custom_fields"), dict):
                normalized["custom_fields"] = {
                    "filters": {},
                    "split": False,
                    "columns": []
                }

            self.restore_optional_data(normalized)

            # 🔥 PREVENT FLICKER
            self.content.update_idletasks()

            for widget in self.content.winfo_children():
                widget.destroy()

            for field, desc in self.fields:
                self.add_card(field, desc)

            self.saved_filters_frame.place_forget()

        except Exception as e:
            print("Apply filter error:", e)



    def _close_dropdown_on_click(self, event):
        if self.saved_filters_frame.winfo_ismapped():
            x1 = self.saved_filters_frame.winfo_rootx()
            y1 = self.saved_filters_frame.winfo_rooty()
            x2 = x1 + self.saved_filters_frame.winfo_width()
            y2 = y1 + self.saved_filters_frame.winfo_height()

            if not (x1 <= event.x_root <= x2 and y1 <= event.y_root <= y2):
                self.saved_filters_frame.place_forget()





    def delete_saved_filter(self, name):
        try:
            delete_preference(name)
            self.render_saved_preferences()
        except Exception as e:
            print("Delete error:", e)
    


    def _fix_custom_fields(self, cf):
        if not isinstance(cf, dict):
            return {"filters": {}, "split": False, "columns": []}

        # 🔥 if nested wrong structure → fix it
        if isinstance(cf.get("filters"), dict) and "filters" in cf["filters"]:
            return {
                "filters": cf["filters"].get("filters", {}),
                "split": cf.get("split", False),
                "columns": cf.get("columns", [])
            }

        return {
            "filters": cf.get("filters", {}),
            "split": cf.get("split", False),
            "columns": cf.get("columns", [])
        }

    def clear_all_filters(self):
        try:
            # reset data
            self.optional_data = {}

            # 🔥 fix custom_fields default
            self.optional_data["custom_fields"] = {
                "filters": {},
                "split": False,
                "columns": []
            }

            # clear UI
            for widget in self.content.winfo_children():
                widget.destroy()

            # rebuild clean form
            for field, desc in self.fields:
                self.add_card(field, desc)

        except Exception as e:
            print("Clear filters error:", e)


