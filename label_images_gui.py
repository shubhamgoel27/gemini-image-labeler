# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "customtkinter",
#     "Pillow",
#     "packaging",
#     "pillow-heif",
# ]
# ///

import os
import csv
import json
import sys
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import pillow_heif
import datetime
from pathlib import Path

# Register HEIC opener
pillow_heif.register_heif_opener()

# --- Configuration & Constants ---
DEFAULT_CATEGORIES = ["cat", "dog", "car", "person", "other"]
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.heic', '.heif'}
CONFIG_FILE = "config.json"
DEFAULT_THEME = "dark-blue"  # Themes: "blue" (standard), "green", "dark-blue"
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme(DEFAULT_THEME)

class ImageLabelerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gemini Image Labeler")
        self.geometry("1100x750")

        # Data State
        self.image_folder = ""
        self.all_image_files = []
        self.image_files = []
        self.current_index = 0
        self.labels = {}  # Map: image_path -> category
        self.categories = list(DEFAULT_CATEGORIES)
        self.csv_file = "image_labels.csv"
        self.hide_labeled_var = tk.BooleanVar(value=True)
        self.history = [] # Stack for undo: list of (image_path, label)
        self.current_rotation = 0

        # Load Configuration
        self.load_config()

        # Layout Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Left) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        # Logo
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Gemini\nLabeler", 
                                     font=ctk.CTkFont(size=22, weight="bold"), justify="left")
        self.logo_label.grid(row=0, column=0, padx=25, pady=(35, 20), sticky="w")

        # Progress Section
        self.progress_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.lbl_progress = ctk.CTkLabel(self.progress_frame, text="Progress: 0%", anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_progress.pack(fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=10)
        self.progress_bar.pack(fill="x", pady=(8, 5))
        self.progress_bar.set(0)
        
        self.lbl_counts = ctk.CTkLabel(self.progress_frame, text="0 / 0", anchor="e", font=ctk.CTkFont(size=11), text_color="gray70")
        self.lbl_counts.pack(fill="x")

        # Actions Group
        self.lbl_actions = ctk.CTkLabel(self.sidebar_frame, text="ACTIONS", anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60")
        self.lbl_actions.grid(row=2, column=0, padx=25, pady=(10, 5), sticky="ew")

        self.btn_open_folder = ctk.CTkButton(self.sidebar_frame, text="📂  Open Folder", command=self.select_folder, anchor="w", height=35)
        self.btn_open_folder.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.btn_change_csv = ctk.CTkButton(self.sidebar_frame, text="📄  Set Label File", command=self.change_label_file, 
                                            anchor="w", height=35, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.btn_change_csv.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        self.btn_organize = ctk.CTkButton(self.sidebar_frame, text="📦  Organize Files", fg_color="#2da44e", hover_color="#2c974b", 
                                          command=self.organize_images, anchor="w", height=35)
        self.btn_organize.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        # Settings Group
        self.lbl_settings = ctk.CTkLabel(self.sidebar_frame, text="SETTINGS", anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray60")
        self.lbl_settings.grid(row=6, column=0, padx=25, pady=(25, 5), sticky="ew")

        self.chk_hide_labeled = ctk.CTkCheckBox(self.sidebar_frame, text="Hide Labeled", variable=self.hide_labeled_var, 
                                                command=self.apply_filter, font=ctk.CTkFont(size=12))
        self.chk_hide_labeled.grid(row=7, column=0, padx=25, pady=8, sticky="w")
        
        self.btn_edit_cats = ctk.CTkButton(self.sidebar_frame, text="✏️  Edit Categories", command=self.open_category_editor, 
                                           anchor="w", height=35, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.btn_edit_cats.grid(row=8, column=0, padx=20, pady=5, sticky="ew")
        
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["System", "Light", "Dark"], 
                                                             command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=9, column=0, padx=20, pady=20, sticky="ew")
        
        # Info Footer
        self.lbl_csv_info = ctk.CTkLabel(self.sidebar_frame, text=f"{Path(self.csv_file).name}", font=ctk.CTkFont(size=10), text_color="gray50")
        self.lbl_csv_info.grid(row=11, column=0, padx=25, pady=(0, 20), sticky="w")

        # --- Main Image Area (Center) ---
        self.image_area_frame = ctk.CTkFrame(self, fg_color=("gray95", "gray10"), corner_radius=0)
        self.image_area_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.image_area_frame.grid_rowconfigure(1, weight=1)
        self.image_area_frame.grid_columnconfigure(0, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self.image_area_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_box.grid(row=0, column=0, sticky="w")
        
        self.lbl_filename = ctk.CTkLabel(self.title_box, text="Welcome", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_filename.pack(anchor="w")
        
        self.lbl_subinfo = ctk.CTkLabel(self.title_box, text="Open a folder to start labeling", font=ctk.CTkFont(size=13), text_color="gray60")
        self.lbl_subinfo.pack(anchor="w")
        
        # Header Tools (Rotate/Trash)
        self.tools_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.tools_frame.grid(row=0, column=1, sticky="e")

        self.btn_rotate_l = ctk.CTkButton(self.tools_frame, text="↺", width=40, height=30, command=lambda: self.rotate_image(90))
        self.btn_rotate_l.pack(side="left", padx=5)
        
        self.btn_rotate_r = ctk.CTkButton(self.tools_frame, text="↻", width=40, height=30, command=lambda: self.rotate_image(-90))
        self.btn_rotate_r.pack(side="left", padx=5)
        
        self.btn_trash = ctk.CTkButton(self.tools_frame, text="🗑️", width=40, height=30, fg_color="#cf222e", hover_color="#a01b24",
                                       command=self.move_to_trash)
        self.btn_trash.pack(side="left", padx=(15, 0))

        # Image Container
        self.image_label = ctk.CTkLabel(self.image_area_frame, text="", corner_radius=0)
        self.image_label.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)

        # Navigation Footer
        self.nav_frame = ctk.CTkFrame(self.image_area_frame, fg_color="transparent")
        self.nav_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(10, 30))
        self.nav_frame.grid_columnconfigure((0, 2), weight=1)
        self.nav_frame.grid_columnconfigure(1, weight=0) # Space between
        
        self.btn_prev = ctk.CTkButton(self.nav_frame, text="⬅️ Previous", command=self.prev_image, 
                                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), width=120, height=35)
        self.btn_prev.grid(row=0, column=0, sticky="w")
        
        self.btn_undo = ctk.CTkButton(self.nav_frame, text="↩ Undo", command=self.undo_last_action,
                                      fg_color="gray50", hover_color="gray40", width=100, height=35)
        self.btn_undo.grid(row=0, column=1, padx=20)
        
        self.btn_next = ctk.CTkButton(self.nav_frame, text="Skip / Next ➡️", command=self.next_image, width=120, height=35)
        self.btn_next.grid(row=0, column=2, sticky="e")

        # --- Right Panel (Categories) ---
        self.cat_outer_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.cat_outer_frame.grid(row=0, column=2, sticky="nsew")
        self.cat_outer_frame.grid_rowconfigure(1, weight=1)
        self.cat_outer_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_cat_title = ctk.CTkLabel(self.cat_outer_frame, text="CATEGORIES", font=ctk.CTkFont(size=13, weight="bold"), anchor="w", text_color="gray60")
        self.lbl_cat_title.grid(row=0, column=0, padx=20, pady=(35, 10), sticky="ew")

        self.cat_frame = ctk.CTkScrollableFrame(self.cat_outer_frame, label_text="", fg_color="transparent")
        self.cat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=0)
        
        # Custom input area fixed at bottom
        self.custom_frame = ctk.CTkFrame(self.cat_outer_frame, fg_color="transparent")
        self.custom_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=20)
        
        self.cat_buttons = []
        
        # Keyboard Bindings
        self.bind("<Left>", lambda e: self.prev_image())
        self.bind("<Right>", lambda e: self.next_image())
        self.bind("<Control-z>", lambda e: self.undo_last_action())

        # Startup
        if self.image_folder and os.path.isdir(self.image_folder):
            self.load_images_from_folder(self.image_folder)
        elif os.path.isdir("images"):
            self.load_images_from_folder("images")
        
        self.load_labels()
        self.refresh_category_buttons()


    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.image_folder = folder
            self.save_config()
            self.load_labels()
            self.load_images_from_folder(folder)

    def change_label_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=os.path.basename(self.csv_file),
            initialdir=os.path.dirname(self.csv_file) if os.path.dirname(self.csv_file) else "."
        )
        if file_path:
            self.csv_file = file_path
            self.lbl_csv_info.configure(text=f"{Path(self.csv_file).name}")
            self.save_config()
            self.load_labels()
            self.display_current_image()

    def organize_images(self):
        if not self.labels:
            messagebox.showinfo("Info", "No labels found to organize.")
            return

        initial_dir = self.image_folder if self.image_folder else "."
        dest_parent = filedialog.askdirectory(title="Select Parent Directory for Organized Folders", initialdir=initial_dir)
        
        if not dest_parent:
            return
            
        target_root = Path(dest_parent) / "labelled_images"
        try:
            target_root.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create folder {target_root}:\n{e}")
            return

        is_move = messagebox.askyesno("Copy or Move?", 
                                      f"Do you want to MOVE the files to:\n{target_root}\n\n"
                                      "Click 'Yes' to MOVE (originals deleted).\n"
                                      "Click 'No' to COPY (originals kept).")
        
        action_verb = "Moving" if is_move else "Copying"
        count = 0
        errors = 0
        skipped = 0
        
        for img_path_str, category in self.labels.items():
            img_path = Path(img_path_str)
            if not img_path.exists():
                if self.image_folder:
                    potential_path = Path(self.image_folder) / img_path.name
                    if potential_path.exists():
                        img_path = potential_path
            
            if img_path.exists():
                cat_folder = target_root / category
                cat_folder.mkdir(parents=True, exist_ok=True)
                dest_file = cat_folder / img_path.name
                
                if dest_file.exists():
                    skipped += 1
                    continue

                try:
                    if is_move:
                        shutil.move(img_path, dest_file)
                    else:
                        shutil.copy2(img_path, dest_file)
                    count += 1
                except Exception as e:
                    print(f"Error {action_verb.lower()} {img_path}: {e}")
                    errors += 1
        
        msg = f"Organization complete.\n{action_verb}: {count} images.\nSkipped (already exists): {skipped}"
        if errors > 0:
            msg += f"\nErrors: {errors}"
        messagebox.showinfo("Done", msg)
        
        if is_move and self.image_folder:
             self.load_images_from_folder(self.image_folder)

    def load_images_from_folder(self, folder):
        self.image_folder = folder
        path = Path(folder)
        self.all_image_files = []
        if path.exists():
            for f in path.iterdir():
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                    self.all_image_files.append(f)
            self.all_image_files.sort()
        
        self.apply_filter()

    def apply_filter(self):
        if self.hide_labeled_var.get():
             self.image_files = [f for f in self.all_image_files if str(f) not in self.labels]
        else:
             self.image_files = list(self.all_image_files)
        
        self.current_index = 0
        self.current_rotation = 0
        self.update_status()
        self.display_current_image()

    def load_labels(self):
        self.labels = {}
        if os.path.exists(self.csv_file):
            try:
                with open(self.csv_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None) # Skip header
                    for row in reader:
                        if row:
                            self.labels[row[0]] = row[1]
            except Exception as e:
                print(f"Error loading labels: {e}")
        self.apply_filter()

    def save_label(self, category):
        if not self.image_files:
            return

        current_file = str(self.image_files[self.current_index])
        
        # Save to history for undo
        self.history.append({'path': current_file, 'label': category, 'index': self.current_index, 'was_hidden': self.hide_labeled_var.get()})
        
        self.labels[current_file] = category
        self.current_rotation = 0 # Reset rotation on save
        
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                 writer.writerow(["image_path", "category", "timestamp"])
            writer.writerow([current_file, category, datetime.datetime.now().isoformat()])
        
        self.refresh_category_buttons() 

        if self.hide_labeled_var.get():
            if self.current_index < len(self.image_files):
                del self.image_files[self.current_index]
            
            if not self.image_files:
                self.update_status()
                self.display_current_image()
                messagebox.showinfo("All Done", "All images in this folder have been labeled!")
                return

            if self.current_index >= len(self.image_files):
                 self.current_index = max(0, len(self.image_files) - 1)
            
            self.update_status()
            self.display_current_image()
        else:
            self.next_image()
            self.update_status()

    def undo_last_action(self):
        if not self.history:
            messagebox.showinfo("Undo", "Nothing to undo!")
            return
            
        last_action = self.history.pop()
        image_path = last_action['path']
        
        # 1. Remove from local labels dict
        if image_path in self.labels:
            del self.labels[image_path]
            
        # 2. Remove from CSV (Rewrite file)
        self.remove_label_from_csv(image_path)
        
        # 3. Restore to view if it was hidden
        # We need to add it back to self.image_files. 
        # Ideally we want it at the same position, or we can just append and sort? 
        # Or simpler: Re-apply filter (which will now see it as unlabeled) and find it.
        # Re-applying filter is robust but resets index. Let's try to be smart.
        
        self.apply_filter() # This puts the image back in self.image_files because we removed it from self.labels
        
        # 4. Find the image index to jump to it
        try:
            # We want to jump back to the image we just undid
            path_obj = Path(image_path)
            # Find index in current image_files
            for i, f in enumerate(self.image_files):
                if str(f) == str(path_obj):
                    self.current_index = i
                    break
        except:
            pass
            
        self.display_current_image()
        self.update_status()

    def remove_label_from_csv(self, image_path_to_remove):
        if not os.path.exists(self.csv_file):
            return
            
        lines = []
        with open(self.csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
                lines.append(header)
                for row in reader:
                    if row and row[0] != str(image_path_to_remove):
                        lines.append(row)
            except StopIteration:
                pass
                
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(lines)

    def move_to_trash(self):
        if not self.image_files:
            return
            
        current_file = self.image_files[self.current_index]
        trash_dir = Path(self.image_folder) / "trash"
        trash_dir.mkdir(exist_ok=True)
        
        try:
            dest = trash_dir / current_file.name
            shutil.move(current_file, dest)
            
            # Remove from all lists
            if current_file in self.all_image_files:
                self.all_image_files.remove(current_file)
            
            # Remove from current view
            del self.image_files[self.current_index]
            
            # Reset index if out of bounds
            if self.current_index >= len(self.image_files):
                self.current_index = max(0, len(self.image_files) - 1)
                
            self.display_current_image()
            self.update_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not move to trash: {e}")

    def rotate_image(self, degrees):
        self.current_rotation = (self.current_rotation + degrees) % 360
        self.display_current_image()

    def display_current_image(self):
        if not self.image_files:
            if self.all_image_files:
                txt = "All images labeled!"
                self.lbl_subinfo.configure(text="Great job! Check the organization tab to move files.")
            else:
                txt = "No images found in folder"
                self.lbl_subinfo.configure(text="Please open a folder containing images.")
            
            self.image_label.configure(text=txt, image=None)
            self.lbl_filename.configure(text="No Image")
            self.current_image_ref = None 
            return

        if 0 <= self.current_index < len(self.image_files):
            file_path = self.image_files[self.current_index]
            current_label = self.labels.get(str(file_path), "Unlabeled")
            
            self.lbl_filename.configure(text=file_path.name)
            self.lbl_subinfo.configure(text=f"Current Status: {current_label}  •  {self.current_index + 1} of {len(self.image_files)}")

            try:
                area_width = self.image_area_frame.winfo_width()
                area_height = self.image_area_frame.winfo_height()
                
                # Subtract padding rough estimate
                area_width -= 60
                area_height -= 40

                if area_width < 100: area_width = 800
                if area_height < 100: area_height = 600

                pil_img = Image.open(file_path)
                
                # Apply rotation
                if self.current_rotation != 0:
                    pil_img = pil_img.rotate(self.current_rotation, expand=True)

                ratio = min(area_width / pil_img.width, area_height / pil_img.height)
                new_width = int(pil_img.width * ratio)
                new_height = int(pil_img.height * ratio)
                
                my_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(new_width, new_height))
                self.current_image_ref = my_image 
                self.image_label.configure(image=my_image, text="")
            except Exception as e:
                self.image_label.configure(image=None, text=f"Error loading image: {e}")
        else:
            self.image_label.configure(text="End of list", image=None)

    def next_image(self):
        self.current_rotation = 0 # Reset rotation
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.display_current_image()
        else:
            messagebox.showinfo("Done", "You have reached the last image.")

    def prev_image(self):
        self.current_rotation = 0 # Reset rotation
        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_image()

    def refresh_category_buttons(self):
        for btn in self.cat_buttons:
            btn.destroy()
        self.cat_buttons = []
        
        if hasattr(self, 'custom_entry') and self.custom_entry:
            self.custom_entry.destroy()
        if hasattr(self, 'btn_custom') and self.btn_custom:
            self.btn_custom.destroy()

        for cat in self.categories:
            btn = ctk.CTkButton(self.cat_frame, text=cat, command=lambda c=cat: self.save_label(c),
                                height=40, font=ctk.CTkFont(size=14))
            btn.pack(pady=5, padx=5, fill="x")
            self.cat_buttons.append(btn)
        
        # Custom Entry - Placed in the fixed bottom frame
        self.custom_frame = ctk.CTkFrame(self.cat_outer_frame, fg_color="transparent")
        self.custom_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=20)
        
        self.custom_entry = ctk.CTkEntry(self.custom_frame, placeholder_text="New Category...", height=35)
        self.custom_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_custom = ctk.CTkButton(self.custom_frame, text="Add", width=60, height=35, 
                                        fg_color="transparent", border_width=1,
                                        command=self.save_custom_category)
        self.btn_custom.pack(side="right")

    def save_custom_category(self):
        cat = self.custom_entry.get().strip()
        if cat:
            if cat not in self.categories:
                self.categories.append(cat)
                self.save_config()
                self.refresh_category_buttons()
            self.save_label(cat)
            self.custom_entry.delete(0, 'end')

    def open_category_editor(self):
        dialog = ctk.CTkInputDialog(text="Enter new categories separated by comma:", title="Edit Categories")
        new_cats_str = dialog.get_input()
        if new_cats_str:
            new_cats = [c.strip() for c in new_cats_str.split(',') if c.strip()]
            if new_cats:
                self.categories = new_cats
                self.save_config()
                self.refresh_category_buttons()

    def update_status(self):
        total = len(self.all_image_files)
        labeled_count = 0
        if self.all_image_files:
             labeled_count = len([f for f in self.all_image_files if str(f) in self.labels])
        
        if total > 0:
            progress = labeled_count / total
        else:
            progress = 0
            
        self.progress_bar.set(progress)
        self.lbl_progress.configure(text=f"Progress: {int(progress*100)}%")
        self.lbl_counts.configure(text=f"{labeled_count} / {total}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.categories = data.get("categories", DEFAULT_CATEGORIES)
                    self.image_folder = data.get("last_folder", "")
                    self.csv_file = data.get("csv_file", "image_labels.csv")
            except:
                pass
    
    def save_config(self):
        data = {
            "categories": self.categories,
            "last_folder": self.image_folder,
            "csv_file": self.csv_file
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

if __name__ == "__main__":
    app = ImageLabelerApp()
    app.mainloop()
