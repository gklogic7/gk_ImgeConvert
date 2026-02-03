import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image
import os

# ---------------- CONFIG ---------------- #
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SUPPORTED_EXT = (".png", ".jpg", ".jpeg", ".webp")

# ---------------- APP (DnD ENABLED) ---------------- #
class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

app = App()
app.title("GK Image Converter & Resizer")
app.geometry("560x520")
app.resizable(False, False)

single_img = None
single_path = None
input_folder = None
output_folder = None

# ---------------- FUNCTIONS ---------------- #

def get_size(orig_w=None, orig_h=None):
    try:
        w = int(width_entry.get())
        h = int(height_entry.get())

        if keep_ratio.get() and orig_w and orig_h:
            ratio = orig_w / orig_h
            h = int(w / ratio)

        return w, h
    except ValueError:
        messagebox.showerror("Error", "Invalid width or height")
        return None

# ---------- DRAG & DROP ---------- #

def drop_image(event):
    global single_img, single_path
    path = event.data.strip("{}")
    if path.lower().endswith(SUPPORTED_EXT):
        single_path = path
        single_img = Image.open(path)
        status_label.configure(text=f"Dropped: {os.path.basename(path)}")

# ---------- SINGLE IMAGE ---------- #

def open_single_image():
    global single_img, single_path
    single_path = filedialog.askopenfilename(
        filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")]
    )
    if single_path:
        single_img = Image.open(single_path)
        status_label.configure(text=f"Loaded: {os.path.basename(single_path)}")

def save_single_image():
    if not single_img:
        messagebox.showerror("Error", "No image loaded")
        return

    size = get_size(single_img.width, single_img.height)
    if not size:
        return

    resized = single_img.resize(size, Image.LANCZOS)

    fmt = format_var.get()
    ext = fmt.lower()

    save_path = filedialog.asksaveasfilename(
        defaultextension=f".{ext}",
        filetypes=[(fmt, f"*.{ext}")]
    )

    if save_path:
        resized.save(save_path, fmt)
        status_label.configure(text="Single image saved ✔")

# ---------- BATCH ---------- #

def select_input_folder():
    global input_folder
    input_folder = filedialog.askdirectory()
    if input_folder:
        batch_status.configure(text=f"Input: {os.path.basename(input_folder)}")

def select_output_folder():
    global output_folder
    output_folder = filedialog.askdirectory()
    if output_folder:
        batch_status.configure(text=f"Output: {os.path.basename(output_folder)}")

def batch_convert():
    if not input_folder or not output_folder:
        messagebox.showerror("Error", "Select input and output folders")
        return

    files = [f for f in os.listdir(input_folder) if f.lower().endswith(SUPPORTED_EXT)]
    if not files:
        messagebox.showerror("Error", "No images found")
        return

    fmt = format_var.get()
    ext = fmt.lower()
    prefix = rename_entry.get() or "gk_"

    progress.set(0)
    step = 1 / len(files)

    for i, file in enumerate(files):
        img_path = os.path.join(input_folder, file)
        img = Image.open(img_path)

        size = get_size(img.width, img.height)
        resized = img.resize(size, Image.LANCZOS)

        name, _ = os.path.splitext(file)
        out_path = os.path.join(output_folder, f"{prefix}{name}.{ext}")
        resized.save(out_path, fmt)

        progress.set((i + 1) * step)
        app.update_idletasks()

    batch_status.configure(text=f"Batch done ✔ {len(files)} images")

# ---------------- UI ---------------- #

title = ctk.CTkLabel(
    app, text="GK Image Converter & Resizer",
    font=ctk.CTkFont(size=20, weight="bold")
)
title.pack(pady=15)

# ---------- SIZE ---------- #

size_frame = ctk.CTkFrame(app)
size_frame.pack(pady=10)

width_entry = ctk.CTkEntry(size_frame, width=90)
width_entry.insert(0, "1024")
width_entry.pack(side="left", padx=5)

height_entry = ctk.CTkEntry(size_frame, width=90)
height_entry.insert(0, "1024")
height_entry.pack(side="left", padx=5)

keep_ratio = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(
    size_frame, text="🔒 Keep Aspect Ratio", variable=keep_ratio
).pack(side="left", padx=10)

# ---------- FORMAT ---------- #

format_var = ctk.StringVar(value="PNG")
ctk.CTkOptionMenu(
    app, values=["PNG", "JPG", "WEBP"], variable=format_var
).pack(pady=10)

# ---------- SINGLE ---------- #

single_frame = ctk.CTkFrame(app)
single_frame.pack(pady=10, fill="x", padx=20)

ctk.CTkLabel(single_frame, text="Single Image (Drag & Drop Supported)").pack(pady=5)

drop_area = ctk.CTkLabel(
    single_frame, text="⬇ Drop Image Here ⬇",
    height=60, corner_radius=10
)
drop_area.pack(pady=5, fill="x", padx=10)
drop_area.drop_target_register(DND_FILES)
drop_area.dnd_bind("<<Drop>>", drop_image)

ctk.CTkButton(single_frame, text="Open Image", command=open_single_image).pack(pady=4)
ctk.CTkButton(single_frame, text="Convert & Save", command=save_single_image).pack(pady=4)

# ---------- BATCH ---------- #

batch_frame = ctk.CTkFrame(app)
batch_frame.pack(pady=10, fill="x", padx=20)

ctk.CTkLabel(batch_frame, text="Batch Convert").pack(pady=5)

rename_entry = ctk.CTkEntry(batch_frame, width=160)
rename_entry.insert(0, "gk_")
rename_entry.pack(pady=4)

ctk.CTkButton(batch_frame, text="Select Input Folder", command=select_input_folder).pack(pady=4)
ctk.CTkButton(batch_frame, text="Select Output Folder", command=select_output_folder).pack(pady=4)
ctk.CTkButton(batch_frame, text="Start Batch Convert", command=batch_convert).pack(pady=6)

progress = ctk.CTkProgressBar(batch_frame, width=360)
progress.pack(pady=6)
progress.set(0)

# ---------- STATUS ---------- #

status_label = ctk.CTkLabel(app, text="Ready", text_color="gray")
status_label.pack()

batch_status = ctk.CTkLabel(app, text="", text_color="gray")
batch_status.pack()

app.mainloop()
