import customtkinter as ctk
from tkinter import filedialog, Canvas, colorchooser
from PIL import Image, ImageTk, ImageEnhance
import os, json
from concurrent.futures import ThreadPoolExecutor

# ================= CONFIG ================= #

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "format": "PNG",
    "keep_ratio": True,
    "prefix": "gk",
    "overlay_text": "gk"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

config = load_config()
SUPPORTED_EXT = (".png", ".jpg", ".jpeg", ".webp")

# ================= APP ================= #

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("GK Image Tool Pro")
app.geometry("1100x620")
app.minsize(900, 520)

single_img = None
single_path = None
input_folder = None
output_folder = None
overlay_img = None

# ================= IMAGE VIEW ================= #

class ImageViewer(Canvas):
    def __init__(self, parent):
        super().__init__(parent, bg="#1e1e1e", highlightthickness=0)
        self.pack(fill="both", expand=True)
        self.img = None
        self.tk_img = None
        self.scale = 1.0
        self.offset = [0, 0]

        self.bind("<MouseWheel>", self.zoom)
        self.bind("<ButtonPress-1>", self.start_pan)
        self.bind("<B1-Motion>", self.pan)

    def load(self, img):
        self.img = img
        self.scale = 1.0
        self.offset = [0, 0]
        self.render()

    def render(self):
        if not self.img:
            return
        w, h = self.img.size
        resized = self.img.resize(
            (int(w * self.scale), int(h * self.scale)),
            Image.LANCZOS
        )
        self.tk_img = ImageTk.PhotoImage(resized)
        self.delete("all")
        self.create_image(
            self.offset[0], self.offset[1],
            anchor="nw", image=self.tk_img
        )

    def zoom(self, e):
        self.scale *= 1.1 if e.delta > 0 else 0.9
        self.render()

    def start_pan(self, e):
        self.last = (e.x, e.y)

    def pan(self, e):
        dx = e.x - self.last[0]
        dy = e.y - self.last[1]
        self.offset[0] += dx
        self.offset[1] += dy
        self.last = (e.x, e.y)
        self.render()

# ================= IMAGE PROCESS ================= #

def apply_adjustments(img):
    img = ImageEnhance.Brightness(img).enhance(brightness.get())
    img = ImageEnhance.Contrast(img).enhance(contrast.get())
    img = ImageEnhance.Color(img).enhance(saturation.get())
    img = ImageEnhance.Sharpness(img).enhance(sharpness.get())
    return img

def resize_image(img):
    w = width_entry.get()
    h = height_entry.get()
    if not w or not h:
        return img
    w, h = int(w), int(h)
    if keep_ratio.get():
        ratio = img.width / img.height
        h = int(w / ratio)
    return img.resize((w, h), Image.LANCZOS)

def apply_overlay(img):
    if overlay_img:
        logo = overlay_img.copy()
        scale = img.width // 6
        logo.thumbnail((scale, scale))
        pos = overlay_pos.get()
        positions = {
            "Top-Left": (10, 10),
            "Top-Right": (img.width - logo.width - 10, 10),
            "Bottom-Left": (10, img.height - logo.height - 10),
            "Bottom-Right": (img.width - logo.width - 10, img.height - logo.height - 10)
        }
        img.paste(logo, positions[pos], logo if logo.mode == "RGBA" else None)
    return img

def process_image(img):
    img = resize_image(img)
    img = apply_adjustments(img)
    img = apply_overlay(img)
    return img

# ================= SINGLE ================= #

def select_image():
    global single_img, single_path
    p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
    if p:
        single_path = p
        single_img = Image.open(p).convert("RGBA")
        viewer.load(single_img)

def save_single():
    if not single_img:
        return
    out = process_image(single_img)
    fmt = format_var.get()
    ext = fmt.lower()
    base = os.path.splitext(os.path.basename(single_path))[0]
    path = filedialog.asksaveasfilename(
        initialfile=f"{config['prefix']}_{base}.{ext}",
        defaultextension=f".{ext}"
    )
    if path:
        out.convert("RGB").save(path, fmt)

# ================= BATCH (MULTITHREAD) ================= #

def select_input_folder():
    global input_folder
    input_folder = filedialog.askdirectory()

def select_output_folder():
    global output_folder
    output_folder = filedialog.askdirectory()

def batch_worker(file_path, out_dir, idx, total):
    img = Image.open(file_path).convert("RGBA")
    out = process_image(img)
    name = os.path.splitext(os.path.basename(file_path))[0]
    out.save(os.path.join(out_dir, f"{config['prefix']}_{name}.{format_var.get().lower()}"))
    progress.set((idx + 1) / total)

def start_batch():
    if not input_folder or not output_folder:
        return
    files = [
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.lower().endswith(SUPPORTED_EXT)
    ]
    total = len(files)
    progress.set(0)
    with ThreadPoolExecutor(max_workers=4) as exe:
        for i, f in enumerate(files):
            exe.submit(batch_worker, f, output_folder, i, total)

# ================= UI ================= #

left = ctk.CTkFrame(app, width=420)
left.pack(side="left", fill="y", padx=8, pady=8)

right = ctk.CTkFrame(app)
right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

viewer = ImageViewer(right)

# Resize
width_entry = ctk.CTkEntry(left, placeholder_text="Width (blank = original)")
width_entry.pack(pady=2)
height_entry = ctk.CTkEntry(left, placeholder_text="Height (blank = original)")
height_entry.pack(pady=2)
keep_ratio = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(left, text="Keep Ratio", variable=keep_ratio).pack(pady=2)

# Color controls
brightness = ctk.DoubleVar(value=1.0)
contrast = ctk.DoubleVar(value=1.0)
saturation = ctk.DoubleVar(value=1.0)
sharpness = ctk.DoubleVar(value=1.0)

for label, var in [
    ("Brightness", brightness),
    ("Contrast", contrast),
    ("Saturation", saturation),
    ("Sharpness", sharpness)
]:
    ctk.CTkLabel(left, text=label).pack()
    ctk.CTkSlider(left, from_=0.5, to=2.0, variable=var).pack(fill="x", padx=10)

# Overlay
overlay_pos = ctk.StringVar(value="Bottom-Right")
ctk.CTkOptionMenu(left, values=[
    "Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"
], variable=overlay_pos).pack(pady=4)

def select_overlay():
    global overlay_img
    p = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
    if p:
        overlay_img = Image.open(p).convert("RGBA")

ctk.CTkButton(left, text="Select Logo Overlay", command=select_overlay).pack(pady=4)

# Buttons
format_var = ctk.StringVar(value="PNG")
ctk.CTkOptionMenu(left, values=["PNG", "JPG", "WEBP"], variable=format_var).pack(pady=4)

ctk.CTkButton(left, text="Select Image", command=select_image).pack(pady=4)
ctk.CTkButton(left, text="Save Single", command=save_single).pack(pady=4)

ctk.CTkLabel(left, text="Batch").pack(pady=6)
ctk.CTkButton(left, text="Select Input Folder", command=select_input_folder).pack(pady=2)
ctk.CTkButton(left, text="Select Output Folder", command=select_output_folder).pack(pady=2)
ctk.CTkButton(left, text="Start Batch (Fast)", command=start_batch).pack(pady=4)

progress = ctk.CTkProgressBar(left)
progress.pack(fill="x", padx=10, pady=6)
progress.set(0)

app.mainloop()
