import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
import os, json

# ================= CONFIG ================= #

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "width": 1024,
    "height": 1024,
    "keep_ratio": True,
    "format": "PNG",
    "language": "en",
    "prefix": "gk_",
    "shortcuts": {
        "open": "<Control-o>",
        "save": "<Control-s>",
        "batch": "<Control-b>",
        "quit": "<Control-q>"
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

config = load_config()

# ================= LANGUAGE ================= #

LANG = {
    "en": {
        "title": "GK Image Converter & Resizer",
        "open": "Open Image",
        "save": "Convert & Save",
        "batch": "Start Batch",
        "drop_img": "⬇ Drop Image Here ⬇",
        "drop_folder": "⬇ Drop Folder Here ⬇",
        "keep": "🔒 Keep Aspect Ratio",
        "settings": "⚙ Settings",
        "preset": "Presets"
    },
    "fr": {
        "title": "GK Convertisseur d’Images",
        "open": "Ouvrir l'image",
        "save": "Convertir & Sauvegarder",
        "batch": "Démarrer le lot",
        "drop_img": "⬇ Déposer l'image ici ⬇",
        "drop_folder": "⬇ Déposer le dossier ici ⬇",
        "keep": "🔒 Conserver le ratio",
        "settings": "⚙ Paramètres",
        "preset": "Préréglages"
    }
}

current_lang = config["language"]
def t(key): return LANG[current_lang][key]

# ================= PRESETS ================= #

PRESETS = {
    "Instagram Post (1:1)": (1080, 1080),
    "Instagram Story / Reel (9:16)": (1080, 1920),
    "YouTube Thumbnail (16:9)": (1280, 720),
    "YouTube Short (9:16)": (1080, 1920),
    "YouTube Banner": (2560, 1440)
}

SUPPORTED_EXT = (".png", ".jpg", ".jpeg", ".webp")

# ================= APP ================= #

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(TkinterDnD.Tk): pass
app = App()
app.geometry("900x540")
app.title(t("title"))
app.resizable(False, False)

single_img = None
single_path = None
preview_imgtk = None
input_folder = None
output_folder = None

# ================= HELPERS ================= #

def persist():
    config.update({
        "width": int(width_entry.get()),
        "height": int(height_entry.get()),
        "keep_ratio": keep_ratio.get(),
        "format": format_var.get(),
        "language": current_lang,
        "prefix": prefix_entry.get()
    })
    save_config(config)

def get_size(w=None, h=None):
    W, H = int(width_entry.get()), int(height_entry.get())
    if keep_ratio.get() and w and h:
        H = int(W * h / w)
    return W, H

def update_preview(img):
    global preview_imgtk
    tmp = img.copy()
    tmp.thumbnail((320, 320))
    preview_imgtk = ImageTk.PhotoImage(tmp)
    preview_label.configure(image=preview_imgtk, text="")

def auto_detect(img):
    w, h = img.size
    if abs(w - h) < 100:
        return PRESETS["Instagram Post (1:1)"]
    return PRESETS["Instagram Story / Reel (9:16)"] if h > w else PRESETS["YouTube Thumbnail (16:9)"]

# ================= SINGLE ================= #

def open_image():
    global single_img, single_path
    p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
    if p:
        single_path = p
        single_img = Image.open(p)
        update_preview(single_img)
        w, h = auto_detect(single_img)
        width_entry.delete(0, "end")
        height_entry.delete(0, "end")
        width_entry.insert(0, w)
        height_entry.insert(0, h)
        persist()

def drop_image(e):
    global single_img, single_path
    p = e.data.strip("{}")
    if p.lower().endswith(SUPPORTED_EXT):
        single_path = p
        single_img = Image.open(p)
        update_preview(single_img)

def save_image():
    if not single_img: return
    w, h = get_size(single_img.width, single_img.height)
    out = single_img.resize((w, h), Image.LANCZOS)
    fmt = format_var.get()
    ext = fmt.lower()
    base = os.path.splitext(os.path.basename(single_path or "image"))[0]
    path = filedialog.asksaveasfilename(
        initialfile=f"{config['prefix']}{base}.{ext}",
        defaultextension=f".{ext}"
    )
    if path:
        out.save(path, fmt)

# ================= BATCH ================= #

def drop_folder(e):
    global input_folder
    p = e.data.strip("{}")
    if os.path.isdir(p):
        input_folder = p
        batch_status.configure(text=os.path.basename(p))

def select_output():
    global output_folder
    output_folder = filedialog.askdirectory()

def batch_convert():
    if not input_folder or not output_folder: return
    files = [f for f in os.listdir(input_folder) if f.lower().endswith(SUPPORTED_EXT)]
    fmt = format_var.get()
    ext = fmt.lower()
    progress.set(0)
    for i, f in enumerate(files):
        img = Image.open(os.path.join(input_folder, f))
        w, h = get_size(img.width, img.height)
        out = img.resize((w, h), Image.LANCZOS)
        name = os.path.splitext(f)[0]
        out.save(os.path.join(output_folder, f"{config['prefix']}{name}.{ext}"), fmt)
        progress.set((i+1)/len(files))
        app.update_idletasks()

# ================= SETTINGS ================= #

def open_settings():
    win = ctk.CTkToplevel(app)
    win.title("Settings")
    win.geometry("360x260")

    def bind(action, entry):
        config["shortcuts"][action] = entry.get()
        save_config(config)
        apply_shortcuts()

    for a in ["open", "save", "batch", "quit"]:
        f = ctk.CTkFrame(win)
        f.pack(pady=6, padx=10, fill="x")
        ctk.CTkLabel(f, text=a.capitalize()).pack(side="left", padx=5)
        e = ctk.CTkEntry(f)
        e.insert(0, config["shortcuts"][a])
        e.pack(side="left", padx=5)
        ctk.CTkButton(f, text="Apply", command=lambda a=a, e=e: bind(a, e)).pack(side="right")

# ================= SHORTCUTS ================= #

def apply_shortcuts():
    app.bind(config["shortcuts"]["open"], lambda e: open_image())
    app.bind(config["shortcuts"]["save"], lambda e: save_image())
    app.bind(config["shortcuts"]["batch"], lambda e: batch_convert())
    app.bind(config["shortcuts"]["quit"], lambda e: app.quit())

apply_shortcuts()

# ================= UI ================= #

top = ctk.CTkFrame(app)
top.pack(fill="x", padx=10, pady=8)

ctk.CTkButton(top, text=t("settings"), command=open_settings, width=110).pack(side="right")

main = ctk.CTkFrame(app)
main.pack(fill="both", expand=True, padx=10, pady=10)

left = ctk.CTkFrame(main, width=380)
left.pack(side="left", fill="y", padx=10)

right = ctk.CTkFrame(main)
right.pack(side="right", fill="both", expand=True)

preview_label = ctk.CTkLabel(right, text="Preview", height=320)
preview_label.pack(pady=20)

width_entry = ctk.CTkEntry(left)
width_entry.insert(0, config["width"])
width_entry.pack(pady=4)

height_entry = ctk.CTkEntry(left)
height_entry.insert(0, config["height"])
height_entry.pack(pady=4)

keep_ratio = ctk.BooleanVar(value=config["keep_ratio"])
ctk.CTkCheckBox(left, text=t("keep"), variable=keep_ratio).pack(pady=4)

format_var = ctk.StringVar(value=config["format"])
ctk.CTkOptionMenu(left, values=["PNG", "JPG", "WEBP"], variable=format_var).pack(pady=4)

preset_menu = ctk.CTkOptionMenu(left, values=list(PRESETS.keys()),
    command=lambda c: (width_entry.delete(0,"end"),
                       height_entry.delete(0,"end"),
                       width_entry.insert(0, PRESETS[c][0]),
                       height_entry.insert(0, PRESETS[c][1])))
preset_menu.pack(pady=4)

drop_img = ctk.CTkLabel(left, text=t("drop_img"), height=60)
drop_img.pack(pady=5, fill="x")
drop_img.drop_target_register(DND_FILES)
drop_img.dnd_bind("<<Drop>>", drop_image)

ctk.CTkButton(left, text=t("open"), command=open_image).pack(pady=3)
ctk.CTkButton(left, text=t("save"), command=save_image).pack(pady=3)

prefix_entry = ctk.CTkEntry(left)
prefix_entry.insert(0, config["prefix"])
prefix_entry.pack(pady=4)

drop_fold = ctk.CTkLabel(left, text=t("drop_folder"), height=60)
drop_fold.pack(pady=5, fill="x")
drop_fold.drop_target_register(DND_FILES)
drop_fold.dnd_bind("<<Drop>>", drop_folder)

ctk.CTkButton(left, text="Select Output Folder", command=select_output).pack(pady=3)
ctk.CTkButton(left, text=t("batch"), command=batch_convert).pack(pady=5)

progress = ctk.CTkProgressBar(left)
progress.pack(pady=4)
progress.set(0)

batch_status = ctk.CTkLabel(left, text="")
batch_status.pack()

app.mainloop()
