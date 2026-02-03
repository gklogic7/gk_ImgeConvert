import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os

# ---------------- LANGUAGE ---------------- #

LANG = {
    "en": {
        "title": "GK Image Converter & Resizer",
        "open": "Open Image",
        "save": "Convert & Save",
        "batch": "Batch Convert",
        "drop_image": "⬇ Drop Image Here ⬇",
        "drop_folder": "⬇ Drop Folder Here ⬇",
        "start_batch": "Start Batch",
        "width": "Width",
        "height": "Height",
        "keep_ratio": "🔒 Keep Aspect Ratio",
        "ready": "Ready"
    },
    "fr": {
        "title": "GK Convertisseur & Redimensionneur",
        "open": "Ouvrir l'image",
        "save": "Convertir & Sauvegarder",
        "batch": "Conversion par lot",
        "drop_image": "⬇ Déposer l'image ici ⬇",
        "drop_folder": "⬇ Déposer le dossier ici ⬇",
        "start_batch": "Démarrer le lot",
        "width": "Largeur",
        "height": "Hauteur",
        "keep_ratio": "🔒 Conserver le ratio",
        "ready": "Prêt"
    }
}

current_lang = "en"

def t(key):
    return LANG[current_lang][key]

# ---------------- APP ---------------- #

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(TkinterDnD.Tk):
    pass

app = App()
app.geometry("900x520")
app.title(t("title"))
app.resizable(False, False)

SUPPORTED_EXT = (".png", ".jpg", ".jpeg", ".webp")

single_img = None
preview_imgtk = None
input_folder = None
output_folder = None

# ---------------- HELPERS ---------------- #

def update_title():
    app.title(t("title"))

def get_size(orig_w=None, orig_h=None):
    try:
        w = int(width_entry.get())
        h = int(height_entry.get())
        if keep_ratio.get() and orig_w and orig_h:
            h = int(w * orig_h / orig_w)
        return w, h
    except:
        messagebox.showerror("Error", "Invalid size")
        return None

def update_preview(img):
    global preview_imgtk
    preview = img.copy()
    preview.thumbnail((300, 300))
    preview_imgtk = ImageTk.PhotoImage(preview)
    preview_label.configure(image=preview_imgtk, text="")

# ---------------- SINGLE IMAGE ---------------- #

def open_image():
    global single_img
    path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
    if path:
        single_img = Image.open(path)
        update_preview(single_img)

def drop_image(event):
    global single_img
    path = event.data.strip("{}")
    if path.lower().endswith(SUPPORTED_EXT):
        single_img = Image.open(path)
        update_preview(single_img)

def save_image():
    if not single_img:
        return
    size = get_size(single_img.width, single_img.height)
    if not size:
        return
    resized = single_img.resize(size, Image.LANCZOS)
    fmt = format_var.get()
    ext = fmt.lower()
    path = filedialog.asksaveasfilename(defaultextension=f".{ext}")
    if path:
        resized.save(path, fmt)

# ---------------- BATCH ---------------- #

def drop_folder(event):
    global input_folder
    path = event.data.strip("{}")
    if os.path.isdir(path):
        input_folder = path
        batch_status.configure(text=os.path.basename(path))

def batch_convert():
    if not input_folder or not output_folder:
        return

    files = [f for f in os.listdir(input_folder) if f.lower().endswith(SUPPORTED_EXT)]
    fmt = format_var.get()
    ext = fmt.lower()
    prefix = rename_entry.get() or "gk_"

    progress.set(0)
    for i, f in enumerate(files):
        img = Image.open(os.path.join(input_folder, f))
        size = get_size(img.width, img.height)
        resized = img.resize(size, Image.LANCZOS)
        name, _ = os.path.splitext(f)
        resized.save(os.path.join(output_folder, f"{prefix}{name}.{ext}"), fmt)
        progress.set((i + 1) / len(files))
        app.update_idletasks()

# ---------------- UI ---------------- #

# Top Bar
top = ctk.CTkFrame(app)
top.pack(fill="x", padx=10, pady=10)

lang_var = ctk.StringVar(value="en")

def switch_lang(choice):
    global current_lang
    current_lang = choice
    update_ui()

ctk.CTkOptionMenu(top, values=["en", "fr"], variable=lang_var, command=switch_lang).pack(side="right")

# Layout
main = ctk.CTkFrame(app)
main.pack(fill="both", expand=True, padx=10, pady=10)

left = ctk.CTkFrame(main, width=350)
left.pack(side="left", fill="y", padx=10)

right = ctk.CTkFrame(main)
right.pack(side="right", fill="both", expand=True)

# Preview
preview_label = ctk.CTkLabel(right, text="Preview", height=300)
preview_label.pack(pady=10)

# Controls
width_entry = ctk.CTkEntry(left, width=80)
width_entry.insert(0, "1024")
width_entry.pack(pady=5)

height_entry = ctk.CTkEntry(left, width=80)
height_entry.insert(0, "1024")
height_entry.pack(pady=5)

keep_ratio = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(left, text=t("keep_ratio"), variable=keep_ratio).pack(pady=5)

format_var = ctk.StringVar(value="PNG")
ctk.CTkOptionMenu(left, values=["PNG", "JPG", "WEBP"], variable=format_var).pack(pady=5)

# Single
drop_img = ctk.CTkLabel(left, text=t("drop_image"), height=60)
drop_img.pack(pady=5)
drop_img.drop_target_register(DND_FILES)
drop_img.dnd_bind("<<Drop>>", drop_image)

ctk.CTkButton(left, text=t("open"), command=open_image).pack(pady=4)
ctk.CTkButton(left, text=t("save"), command=save_image).pack(pady=4)

# Batch
rename_entry = ctk.CTkEntry(left)
rename_entry.insert(0, "gk_")
rename_entry.pack(pady=5)

drop_fold = ctk.CTkLabel(left, text=t("drop_folder"), height=60)
drop_fold.pack(pady=5)
drop_fold.drop_target_register(DND_FILES)
drop_fold.dnd_bind("<<Drop>>", drop_folder)

ctk.CTkButton(left, text=t("start_batch"), command=batch_convert).pack(pady=6)

progress = ctk.CTkProgressBar(left)
progress.pack(pady=5)
progress.set(0)

batch_status = ctk.CTkLabel(left, text="")
batch_status.pack()

# ---------------- SHORTCUTS ---------------- #

app.bind("<Control-o>", lambda e: open_image())
app.bind("<Control-s>", lambda e: save_image())
app.bind("<Control-b>", lambda e: batch_convert())
app.bind("<Control-q>", lambda e: app.quit())

# ---------------- LANGUAGE REFRESH ---------------- #

def update_ui():
    update_title()
    drop_img.configure(text=t("drop_image"))
    drop_fold.configure(text=t("drop_folder"))

update_ui()
app.mainloop()
