import customtkinter as ctk
from tkinter import filedialog, Canvas
from PIL import Image, ImageTk
import os, json

# ================= CONFIG ================= #

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "format": "PNG",
    "keep_ratio": True,
    "prefix": "gk_"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

config = load_config()

SUPPORTED_EXT = (".png", ".jpg", ".jpeg", ".webp")

PRESETS = {
    "Instagram Post (1:1)": (1080, 1080),
    "Instagram Story / Reel (9:16)": (1080, 1920),
    "YouTube Thumbnail (16:9)": (1280, 720)
}

# ================= APP ================= #

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("GK Image Tool Pro")
app.geometry("980x560")
app.resizable(False, False)

single_img = None
single_path = None
input_folder = None
output_folder = None

# ================= IMAGE VIEW (ZOOM + PAN) ================= #

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

# ================= HELPERS ================= #

def get_resize_size(img):
    w = width_entry.get()
    h = height_entry.get()

    if not w or not h:
        return img.size

    w, h = int(w), int(h)

    if keep_ratio.get():
        ratio = img.width / img.height
        h = int(w / ratio)

    return w, h

# ================= SINGLE IMAGE ================= #

def select_image():
    global single_img, single_path
    p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
    if p:
        single_path = p
        single_img = Image.open(p)
        viewer.load(single_img)

def save_single():
    if not single_img:
        return

    size = get_resize_size(single_img)
    out = single_img.resize(size, Image.LANCZOS)

    fmt = format_var.get()
    ext = fmt.lower()
    base = os.path.splitext(os.path.basename(single_path))[0]

    path = filedialog.asksaveasfilename(
        initialfile=f"{config['prefix']}{base}.{ext}",
        defaultextension=f".{ext}"
    )
    if path:
        out.save(path, fmt)

# ================= BATCH ================= #

def select_input_folder():
    global input_folder
    input_folder = filedialog.askdirectory()

def select_output_folder():
    global output_folder
    output_folder = filedialog.askdirectory()

def batch_convert():
    if not input_folder or not output_folder:
        return

    files = [f for f in os.listdir(input_folder) if f.lower().endswith(SUPPORTED_EXT)]
    fmt = format_var.get()
    ext = fmt.lower()

    progress.set(0)
    for i, f in enumerate(files):
        img = Image.open(os.path.join(input_folder, f))
        size = get_resize_size(img)
        out = img.resize(size, Image.LANCZOS)
        name = os.path.splitext(f)[0]
        out.save(os.path.join(output_folder, f"{config['prefix']}{name}.{ext}"), fmt)
        progress.set((i + 1) / len(files))
        app.update_idletasks()

# ================= UI ================= #

left = ctk.CTkFrame(app, width=380)
left.pack(side="left", fill="y", padx=10, pady=10)

right = ctk.CTkFrame(app)
right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

viewer = ImageViewer(right)

width_entry = ctk.CTkEntry(left, placeholder_text="Width (blank = original)")
width_entry.pack(pady=4)

height_entry = ctk.CTkEntry(left, placeholder_text="Height (blank = original)")
height_entry.pack(pady=4)

keep_ratio = ctk.BooleanVar(value=config["keep_ratio"])
ctk.CTkCheckBox(left, text="🔒 Keep Aspect Ratio", variable=keep_ratio).pack(pady=4)

format_var = ctk.StringVar(value=config["format"])
ctk.CTkOptionMenu(left, values=["PNG", "JPG", "WEBP"], variable=format_var).pack(pady=4)

ctk.CTkOptionMenu(
    left, values=list(PRESETS.keys()),
    command=lambda c: (
        width_entry.delete(0, "end"),
        height_entry.delete(0, "end"),
        width_entry.insert(0, PRESETS[c][0]),
        height_entry.insert(0, PRESETS[c][1])
    )
).pack(pady=6)

ctk.CTkButton(left, text="Select Image", command=select_image).pack(pady=6)
ctk.CTkButton(left, text="Save Single Image", command=save_single).pack(pady=6)

ctk.CTkLabel(left, text="Batch").pack(pady=10)
ctk.CTkButton(left, text="Select Input Folder", command=select_input_folder).pack(pady=4)
ctk.CTkButton(left, text="Select Output Folder", command=select_output_folder).pack(pady=4)
ctk.CTkButton(left, text="Start Batch Convert", command=batch_convert).pack(pady=6)

progress = ctk.CTkProgressBar(left)
progress.pack(pady=4)
progress.set(0)

app.mainloop()
