import customtkinter as ctk
from tkinter import filedialog, Canvas, colorchooser
from PIL import Image, ImageTk, ImageEnhance, ImageDraw, ImageFont
import os
from concurrent.futures import ThreadPoolExecutor

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("GK Image Tool Pro")
app.geometry("1200x700")
app.minsize(1000, 600)

# ================= STATE ================= #

original_img = None        # untouched
preview_img = None         # live preview base
display_img = None         # final shown
tk_img = None

overlay_logo = None
logo_pos = [50, 50]

text_overlay = "gk"
text_pos = [100, 100]
text_color = (255, 255, 255)
font_size = 32

crop_rect = None
crop_start = None

# ================= VIEWER ================= #

class ImageViewer(Canvas):
    def __init__(self, parent):
        super().__init__(parent, bg="#1e1e1e", highlightthickness=0)
        self.pack(fill="both", expand=True)

        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.release)

    def show(self, img):
        global tk_img
        self.delete("all")
        self.img = img
        tk_img = ImageTk.PhotoImage(img)
        self.create_image(0, 0, anchor="nw", image=tk_img)

        if crop_rect:
            self.create_rectangle(*crop_rect, outline="red", width=2)

    def start_drag(self, e):
        global crop_start
        crop_start = (e.x, e.y)

    def drag(self, e):
        global crop_rect
        crop_rect = (crop_start[0], crop_start[1], e.x, e.y)
        self.show(display_img)

    def release(self, e):
        pass

viewer = ImageViewer(app)

# ================= IMAGE PROCESS ================= #

def apply_live_preview(*_):
    global display_img
    if not original_img:
        return

    img = original_img.copy()

    img = ImageEnhance.Brightness(img).enhance(brightness.get())
    img = ImageEnhance.Contrast(img).enhance(contrast.get())
    img = ImageEnhance.Color(img).enhance(saturation.get())
    img = ImageEnhance.Sharpness(img).enhance(sharpness.get())

    draw = ImageDraw.Draw(img)

    if overlay_logo:
        logo = overlay_logo.copy()
        logo.thumbnail((img.width // 6, img.height // 6))
        img.paste(logo, logo_pos, logo)

    if text_overlay:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        draw.text(text_pos, text_overlay, fill=text_color, font=font)

    display_img = img
    viewer.show(display_img)

# ================= LOAD IMAGE ================= #

def select_image():
    global original_img
    p = filedialog.askopenfilename(
        filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")]
    )
    if p:
        original_img = Image.open(p).convert("RGBA")
        apply_live_preview()

# ================= LOGO ================= #

def select_logo():
    global overlay_logo
    p = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
    if p:
        overlay_logo = Image.open(p).convert("RGBA")
        apply_live_preview()

# ================= TEXT ================= #

def choose_text_color():
    global text_color
    c = colorchooser.askcolor()[0]
    if c:
        text_color = tuple(map(int, c))
        apply_live_preview()

# ================= CROP ================= #

def apply_crop():
    global original_img, crop_rect
    if crop_rect and original_img:
        x1, y1, x2, y2 = crop_rect
        original_img = original_img.crop((x1, y1, x2, y2))
        crop_rect = None
        apply_live_preview()

# ================= SAVE ================= #

def save_image():
    if not display_img:
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG", "*.png"), ("JPG", "*.jpg"), ("WEBP", "*.webp")]
    )
    if path:
        display_img.convert("RGB").save(path)

# ================= UI ================= #

controls = ctk.CTkFrame(app, width=300)
controls.pack(side="right", fill="y", padx=8, pady=8)

def slider(label, var, f, t):
    ctk.CTkLabel(controls, text=label).pack()
    ctk.CTkSlider(
        controls, from_=f, to=t,
        variable=var, command=apply_live_preview
    ).pack(fill="x", padx=10)

brightness = ctk.DoubleVar(value=1)
contrast = ctk.DoubleVar(value=1)
saturation = ctk.DoubleVar(value=1)
sharpness = ctk.DoubleVar(value=1)

slider("Brightness", brightness, 0.5, 1.5)
slider("Contrast", contrast, 0.5, 1.5)
slider("Saturation", saturation, 0.5, 1.5)
slider("Sharpness", sharpness, 0.5, 2.0)

ctk.CTkButton(controls, text="Select Image", command=select_image).pack(pady=6)
ctk.CTkButton(controls, text="Select Logo", command=select_logo).pack(pady=4)

text_entry = ctk.CTkEntry(controls, placeholder_text="Overlay Text")
text_entry.insert(0, "gk")
text_entry.pack(pady=4)

def update_text():
    global text_overlay
    text_overlay = text_entry.get()
    apply_live_preview()

ctk.CTkButton(controls, text="Update Text", command=update_text).pack(pady=2)
ctk.CTkButton(controls, text="Text Color", command=choose_text_color).pack(pady=2)

ctk.CTkLabel(controls, text="Font Size").pack()
ctk.CTkSlider(
    controls, from_=10, to=100,
    command=lambda v: (
        globals().__setitem__("font_size", int(float(v))),
        apply_live_preview()
    )
).pack(fill="x", padx=10)

ctk.CTkButton(controls, text="Apply Crop", command=apply_crop).pack(pady=6)
ctk.CTkButton(controls, text="Save Image", command=save_image).pack(pady=10)

app.mainloop()
