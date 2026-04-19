import json
import tkinter as tk
from math import ceil

import customtkinter as ctk
import pyautogui
from PIL import Image
from customtkinter import CTkImage
from utils import load_toml_as_dict, save_brawler_icon, get_dpi_scale, save_dict_as_toml
from tkinter import filedialog

orig_screen_width, orig_screen_height = 1920, 1080
width, height = pyautogui.size()
width_ratio = width / orig_screen_width
height_ratio = height / orig_screen_height
scale_factor = min(width_ratio, height_ratio)
scale_factor *= 96/get_dpi_scale()
pyla_version = load_toml_as_dict("./cfg/general_config.toml")['pyla_version']

class SelectBrawler:

    def __init__(self, data_setter, brawlers):
        self.app = ctk.CTk()

        square_size = int(75 * scale_factor)
        amount_of_rows = ceil(len(brawlers)/10) + 1
        necessary_height = (int(145 * scale_factor) + amount_of_rows*square_size + (amount_of_rows-1)*int(3 * scale_factor))
        self.app.title(f"PylaAI v{pyla_version}")
        self.brawlers = brawlers

        self.app.geometry(f"{str(int(860 * scale_factor))}x{necessary_height}+{str(int(600 * scale_factor))}")
        self.data_setter = data_setter
        self.colors = {
            'gray': "#7d7777",
            'red': "#cd5c5c",
            'darker_white': '#c4c4c4',
            'dark gray': '#1c1c1c',
            'cherry red': '#960a00',
            'ui box gray': '#242424',
            'chess white': '#f0d9b5',
            'chess brown': '#b58863',
            'indian red': "#cd5c5c"
        }

        self.app.configure(fg_color=self.colors['ui box gray'])



        self.images = []
        self.brawlers_data = []
        self.farm_type = ""

        for brawler in self.brawlers:
            img_path = f"./api/assets/brawler_icons/{brawler}.png"
            try:
                img = Image.open(img_path)
            except FileNotFoundError:
                save_brawler_icon(brawler)
                img = Image.open(img_path)

            img_tk = CTkImage(img, size=(square_size, square_size))
            self.images.append((brawler, img_tk))  # Store tuple of brawler name and image

        # Entry widget for filtering
        self.filter_var = tk.StringVar()
        self.filter_entry = ctk.CTkEntry(
            self.app, textvariable=self.filter_var,
            placeholder_text="Type brawler name...", font=("", int(20 * scale_factor)), width=int(200 * scale_factor),
            fg_color=self.colors['ui box gray'], border_color=self.colors['cherry red'], text_color="white"
        )
        ctk.CTkLabel(self.app, text="Write brawler", font=("Comic sans MS", int(20 * scale_factor)),
                     text_color=self.colors['cherry red']).place(x=int(scale_factor * 373), y=int(scale_factor * 20))
        self.filter_entry.place(x=int(340 * scale_factor), y=int(scale_factor * 52))
        self.filter_var.trace_add("write", lambda *args: self.update_images(self.filter_var.get()))

        # Frame to hold the images
        self.image_frame = ctk.CTkFrame(self.app, fg_color=self.colors['ui box gray'])
        self.image_frame.place(x=0, y=int(100 * scale_factor))

        self.update_images("")
        ctk.CTkButton(self.app, text="Start", command=self.start_bot, fg_color=self.colors['ui box gray'],
                      text_color="white",
                      font=("Comic sans MS", int(25 * scale_factor)), border_color=self.colors['cherry red'],
                      border_width=int(2 * scale_factor)).place(x=int(390 * scale_factor), y=int((necessary_height-60* scale_factor) ))

        ctk.CTkButton(self.app, text="Load Brawler Config", command=self.load_brawler_config, fg_color=self.colors['ui box gray'],
                      text_color="white",
                      font=("Comic sans MS", int(25 * scale_factor)), border_color=self.colors['cherry red'],
                      border_width=int(2 * scale_factor)).place(x=int(10 * scale_factor),
                                                                y=int((necessary_height-60* scale_factor) ))

        self.timer_var = tk.StringVar()
        self.timer_entry = ctk.CTkEntry(
            self.app, textvariable=self.timer_var,
            placeholder_text="Enter an amount of minutes", font=("", int(20 * scale_factor)), width=int(80 * scale_factor),
            fg_color=self.colors['ui box gray'], border_color=self.colors['cherry red'], text_color="white"
        )
        ctk.CTkLabel(self.app, text="Run for :", font=("Comic sans MS", int(22 * scale_factor)),
                     text_color="white").place(x=int(scale_factor * 580), y=int((necessary_height-55* scale_factor) ))
        self.timer_entry.place(x=int(scale_factor * 675), y=int((necessary_height-55* scale_factor) ))
        self.timer_var.set(load_toml_as_dict("cfg/general_config.toml")["run_for_minutes"])
        self.timer_var.trace_add("write", lambda *args: self.update_timer(self.timer_var.get()))
        ctk.CTkLabel(self.app, text="minutes", font=("Comic sans MS", int(22 * scale_factor)),
                     text_color="white").place(x=int(scale_factor * 760), y=int((necessary_height-55* scale_factor) ))

        self.app.mainloop()

    def set_farm_type(self, value):
        self.farm_type = value

    def start_bot(self):
        self.data_setter(self.brawlers_data)
        self.app.destroy()

    def load_brawler_config(self):
        # open file select dialog to select a json file
        file_path = filedialog.askopenfilename(
            title="Select Brawler Config File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    brawlers_data = json.load(file)
                    try:
                        brawlers_data = [
                            bd for bd in brawlers_data
                            if not (bd["push_until"] <= bd[bd["type"]])
                        ]
                        self.brawlers_data = brawlers_data
                        print("Brawler data loaded successfully :", brawlers_data)
                    except Exception as e:
                        print("Invalid data format. Expected a list of brawler data.", e)
            except Exception as e:
                print(f"Error loading brawler data: {e}")

    def on_image_click(self, brawler):
        self.open_brawler_entry(brawler)

    def open_brawler_entry(self, brawler):
        top = ctk.CTkToplevel(self.app)
        top.configure(fg_color=self.colors['ui box gray'])
        win_w = int(300 * scale_factor)
        win_h = int(400 * scale_factor)
        top.geometry(
            f"{win_w}x{win_h}+{str(int(1100 * scale_factor))}+{str(int(200 * scale_factor))}")
        top.title("Enter Brawler Data")
        top.attributes("-topmost", True)

        # --- Variables ---
        push_until_var = tk.StringVar()
        trophies_var = tk.StringVar()
        wins_var = tk.StringVar()
        current_win_streak_var = tk.StringVar(value="0")
        auto_pick_var = tk.BooleanVar(value=True) if self.brawlers_data else tk.BooleanVar(value=False)

        # --- Fixed Y positions for placed widgets ---
        y_title = int(7 * scale_factor)
        y_buttons = int(50 * scale_factor)
        y_field1_label = int(100 * scale_factor)
        y_field1_entry = int(125 * scale_factor)
        y_field2_label = int(165 * scale_factor)
        y_field2_entry = int(190 * scale_factor)
        y_field3_label = int(230 * scale_factor)
        y_field3_entry = int(255 * scale_factor)
        y_auto_pick = int(300 * scale_factor)
        y_submit = int(350 * scale_factor)
        x_center_label = int(70 * scale_factor)
        x_center_entry = int(60 * scale_factor)
        entry_width = int(170 * scale_factor)

        # --- Title ---
        ctk.CTkLabel(top, text=f"Brawler: {brawler}", font=("Comic sans MS", int(20 * scale_factor)),
                     text_color=self.colors['red']).place(x=x_center_label, y=y_title)

        # --- Push type buttons ---
        farm_type_button_frame = ctk.CTkFrame(top, width=int(210 * scale_factor), height=int(40 * scale_factor),
                                              fg_color=self.colors['ui box gray'])
        farm_type_button_frame.place(x=int(45 * scale_factor), y=y_buttons)

        # --- Entry widgets (created but NOT placed yet) ---
        push_until_label = ctk.CTkLabel(top, text="Target Amount", font=("Comic sans MS", int(15 * scale_factor)),
                     text_color=self.colors['chess white'])
        push_until_entry = ctk.CTkEntry(
            top, textvariable=push_until_var, fg_color=self.colors['ui box gray'], text_color="white",
            border_color=self.colors['cherry red'], border_width=int(2 * scale_factor),
            height=int(28 * scale_factor), width=entry_width
        )

        trophies_label = ctk.CTkLabel(top, text="Current Trophies", font=("Comic sans MS", int(15 * scale_factor)),
                     text_color=self.colors['chess white'])
        trophies_entry = ctk.CTkEntry(
            top, textvariable=trophies_var, fg_color=self.colors['ui box gray'], text_color="white",
            border_color=self.colors['cherry red'], border_width=int(2 * scale_factor),
            height=int(28 * scale_factor), width=entry_width
        )

        wins_label = ctk.CTkLabel(top, text="Current Wins", font=("Comic sans MS", int(15 * scale_factor)),
                     text_color=self.colors['chess white'])
        wins_entry = ctk.CTkEntry(
            top, textvariable=wins_var, fg_color=self.colors['ui box gray'], text_color="white",
            border_color=self.colors['cherry red'], border_width=int(2 * scale_factor),
            height=int(28 * scale_factor), width=entry_width
        )

        win_streak_label = ctk.CTkLabel(top, text="Current Brawler's Win Streak", font=("Comic sans MS", int(15 * scale_factor)),
                     text_color=self.colors['chess white'])
        current_win_streak_entry = ctk.CTkEntry(
            top, textvariable=current_win_streak_var, fg_color=self.colors['ui box gray'], text_color="white",
            border_color=self.colors['cherry red'], border_width=int(2 * scale_factor),
            height=int(28 * scale_factor), width=entry_width
        )

        auto_pick_checkbox = ctk.CTkCheckBox(
            top, text="Bot auto-selects brawler", variable=auto_pick_var,
            fg_color=self.colors['cherry red'], text_color="white", checkbox_height=int(24 * scale_factor)
        )

        def submit_data():
            push_until_raw = push_until_var.get()
            push_until_value = int(push_until_raw) if push_until_raw.isdigit() else 0
            trophies_raw = trophies_var.get()
            trophies_value = int(trophies_raw) if trophies_raw.isdigit() else 0
            wins_raw = wins_var.get()
            wins_value = int(wins_raw) if wins_raw.isdigit() else 0
            current_win_streak_raw = current_win_streak_var.get()
            current_win_streak_value = int(current_win_streak_raw) if current_win_streak_raw.isdigit() else 0
            data = {
                "brawler": brawler,
                "push_until": push_until_value,
                "trophies": trophies_value,
                "wins": wins_value,
                "type": self.farm_type,
                "automatically_pick": auto_pick_var.get(),
                "win_streak": current_win_streak_value
            }

            self.brawlers_data = [item for item in self.brawlers_data if item["brawler"] != data["brawler"]]
            self.brawlers_data.append(data)

            print("Selected Brawler Data :", self.brawlers_data)
            top.destroy()

        submit_button = ctk.CTkButton(
            top, text="Submit", command=submit_data, fg_color=self.colors['ui box gray'],
            border_color=self.colors['cherry red'],
            text_color="white", border_width=int(2 * scale_factor), width=int(80 * scale_factor)
        )

        # --- All dynamic widgets that can be shown/hidden ---
        all_dynamic_widgets = [
            push_until_label, push_until_entry,
            trophies_label, trophies_entry,
            wins_label, wins_entry,
            win_streak_label, current_win_streak_entry,
            auto_pick_checkbox, submit_button
        ]

        def hide_all_fields():
            for w in all_dynamic_widgets:
                w.place_forget()

        def check_submit_visibility():
            """Show submit only when push type is selected and required numeric fields are filled."""
            if self.farm_type == "":
                submit_button.place_forget()
                return
            target_ok = push_until_var.get().isdigit()
            if self.farm_type == "trophies":
                fields_ok = target_ok and trophies_var.get().isdigit() and current_win_streak_var.get().isdigit()
            else:  # wins
                fields_ok = target_ok and wins_var.get().isdigit()
            if fields_ok:
                submit_button.place(x=int(110 * scale_factor), y=y_submit)
            else:
                submit_button.place_forget()

        # Trace all entry vars to re-check submit visibility on every keystroke
        push_until_var.trace_add("write", lambda *a: check_submit_visibility())
        trophies_var.trace_add("write", lambda *a: check_submit_visibility())
        wins_var.trace_add("write", lambda *a: check_submit_visibility())
        current_win_streak_var.trace_add("write", lambda *a: check_submit_visibility())

        def show_trophies_fields():
            hide_all_fields()
            self.farm_type = "trophies"
            self.wins_button.configure(fg_color=self.colors['ui box gray'])
            self.trophies_button.configure(fg_color=self.colors['cherry red'])
            # Field 1: Target Amount
            push_until_label.place(x=x_center_label, y=y_field1_label)
            push_until_entry.place(x=x_center_entry, y=y_field1_entry)
            # Field 2: Current Trophies
            trophies_label.place(x=x_center_label, y=y_field2_label)
            trophies_entry.place(x=x_center_entry, y=y_field2_entry)
            # Field 3: Win Streak
            win_streak_label.place(x=int(40 * scale_factor), y=y_field3_label)
            current_win_streak_entry.place(x=x_center_entry, y=y_field3_entry)
            # Auto-pick checkbox
            auto_pick_checkbox.place(x=int(60 * scale_factor), y=y_auto_pick)
            check_submit_visibility()

        def show_wins_fields():
            hide_all_fields()
            self.farm_type = "wins"
            self.wins_button.configure(fg_color=self.colors['cherry red'])
            self.trophies_button.configure(fg_color=self.colors['ui box gray'])
            # Field 1: Target Amount
            push_until_label.place(x=x_center_label, y=y_field1_label)
            push_until_entry.place(x=x_center_entry, y=y_field1_entry)
            # Field 2: Current Wins
            wins_label.place(x=x_center_label, y=y_field2_label)
            wins_entry.place(x=x_center_entry, y=y_field2_entry)
            # Auto-pick checkbox
            auto_pick_checkbox.place(x=int(60 * scale_factor), y=y_auto_pick)
            check_submit_visibility()

        self.wins_button = ctk.CTkButton(farm_type_button_frame, text="Win Amount", width=int(90 * scale_factor),
                                            command=show_wins_fields,
                                            hover_color=self.colors['cherry red'],
                                            font=("", int(15 * scale_factor)),
                                            fg_color=self.colors["ui box gray"],
                                            border_color=self.colors['cherry red'],
                                            border_width=int(2 * scale_factor)
                                            )
        self.trophies_button = ctk.CTkButton(farm_type_button_frame, text="Trophies", width=int(85 * scale_factor),
                                             command=show_trophies_fields,
                                             hover_color=self.colors['cherry red'],
                                             font=("", int(15 * scale_factor)),
                                             fg_color=self.colors["ui box gray"],
                                             border_color=self.colors['cherry red'], border_width=int(2 * scale_factor)
                                             )

        self.trophies_button.place(x=int(10 * scale_factor))
        self.wins_button.place(x=int(110 * scale_factor))


    def update_images(self, filter_text):
        for widget in self.image_frame.winfo_children():
            widget.destroy()

        row_num = 0
        col_num = 0

        for brawler, img_tk in self.images:
            if brawler.startswith(filter_text.lower()):
                label = ctk.CTkLabel(self.image_frame, image=img_tk, text="")
                label.bind("<Button-1>", lambda e, b=brawler: self.on_image_click(b))  # Bind click event
                label.grid(row=row_num, column=col_num, padx=int(5 * scale_factor), pady=int(3 * scale_factor))

                col_num += 1
                if col_num == 10:  # Move to the next row after 10 columns
                    col_num = 0
                    row_num += 1

    def update_timer(self, value):
        try:
            minutes = int(value)
            config = load_toml_as_dict("cfg/general_config.toml")
            config['run_for_minutes'] = minutes
            save_dict_as_toml(config, "cfg/general_config.toml", )
        except ValueError:
            pass  # Ignore invalid input

def dummy_data_setter(data):
    print("Data set:", data)
