import customtkinter as ctk
from tkinter import filedialog, Canvas
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import os
import json
from threading import Thread
from queue import Queue
import traceback

# ================= CONFIG ================= #
#Code From Claude 
#Not Working 

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "format": "PNG",
    "keep_ratio": True,
    "prefix": "gk_",
    "brightness": 1.0,
    "contrast": 1.0,
    "saturation": 1.0,
    "sharpness": 1.0
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=4)
    except:
        pass

config = load_config()

SUPPORTED_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")

PRESETS = {
    "Instagram Post (1:1)": (1080, 1080),
    "Instagram Story / Reel (9:16)": (1080, 1920),
    "YouTube Thumbnail (16:9)": (1280, 720),
    "Facebook Post (1200x630)": (1200, 630),
    "Twitter Post (1200x675)": (1200, 675)
}

# ================= APP ================= #

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("GK Image Tool Pro - Enhanced")
app.geometry("1200x700")
app.resizable(True, True)

# Global variables
single_img = None
single_path = None
input_folder = None
output_folder = None
preview_queue = Queue()
is_processing = False

# ================= IMAGE PROCESSING ================= #

def apply_adjustments(img, brightness=1.0, contrast=1.0, saturation=1.0, sharpness=1.0):
    """Apply color corrections to image safely"""
    try:
        if img is None or img.size[0] == 0 or img.size[1] == 0:
            return img
        
        # Convert to RGB if needed
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        
        # Apply brightness
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        
        # Apply contrast
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        # Apply saturation
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation)
        
        # Apply sharpness
        if sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(sharpness)
        
        return img
    except Exception as e:
        print(f"Error applying adjustments: {e}")
        return img

def get_current_adjustments():
    """Get current slider values safely"""
    try:
        return {
            'brightness': brightness_slider.get(),
            'contrast': contrast_slider.get(),
            'saturation': saturation_slider.get(),
            'sharpness': sharpness_slider.get()
        }
    except:
        return {
            'brightness': 1.0,
            'contrast': 1.0,
            'saturation': 1.0,
            'sharpness': 1.0
        }

# ================= IMAGE VIEWER (ZOOM + PAN) ================= #

class ImageViewer(Canvas):
    def __init__(self, parent):
        super().__init__(parent, bg="#1e1e1e", highlightthickness=0)
        self.pack(fill="both", expand=True)
        self.img = None
        self.tk_img = None
        self.scale = 1.0
        self.offset = [0, 0]
        self.dragging = False

        self.bind("<MouseWheel>", self.zoom)
        self.bind("<ButtonPress-1>", self.start_pan)
        self.bind("<B1-Motion>", self.pan)
        self.bind("<ButtonRelease-1>", self.end_pan)
        
        # For trackpad/Linux
        self.bind("<Button-4>", lambda e: self.zoom_in())
        self.bind("<Button-5>", lambda e: self.zoom_out())

    def load(self, img):
        """Load image safely"""
        try:
            if img is None:
                return
            self.img = img.copy()
            self.scale = 1.0
            self.offset = [0, 0]
            self.render()
        except Exception as e:
            print(f"Error loading image: {e}")

    def render(self):
        """Render image with current scale and offset"""
        try:
            if not self.img or self.img.size[0] == 0:
                return
            
            w, h = self.img.size
            new_w = max(1, int(w * self.scale))
            new_h = max(1, int(h * self.scale))
            
            # Use LANCZOS for downscaling, BILINEAR for upscaling (faster)
            resampling = Image.LANCZOS if self.scale < 1.0 else Image.BILINEAR
            resized = self.img.resize((new_w, new_h), resampling)
            
            self.tk_img = ImageTk.PhotoImage(resized)
            self.delete("all")
            self.create_image(
                self.offset[0], self.offset[1],
                anchor="nw", image=self.tk_img
            )
        except Exception as e:
            print(f"Error rendering: {e}")

    def zoom(self, e):
        try:
            if e.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        except:
            pass

    def zoom_in(self):
        self.scale = min(self.scale * 1.1, 10.0)
        self.render()

    def zoom_out(self):
        self.scale = max(self.scale * 0.9, 0.1)
        self.render()

    def start_pan(self, e):
        self.last = (e.x, e.y)
        self.dragging = True

    def pan(self, e):
        if self.dragging:
            dx = e.x - self.last[0]
            dy = e.y - self.last[1]
            self.offset[0] += dx
            self.offset[1] += dy
            self.last = (e.x, e.y)
            self.render()

    def end_pan(self, e):
        self.dragging = False

# ================= HELPERS ================= #

def get_resize_size(img):
    """Get target resize dimensions safely"""
    try:
        w = width_entry.get().strip()
        h = height_entry.get().strip()

        if not w or not h:
            return img.size

        w, h = int(w), int(h)

        if keep_ratio.get() and w > 0:
            ratio = img.width / img.height
            h = max(1, int(w / ratio))

        return max(1, w), max(1, h)
    except:
        return img.size

def update_preview():
    """Update preview with current adjustments - debounced"""
    if not single_img or is_processing:
        return
    
    # Add to queue
    preview_queue.put(True)
    
    # Process after short delay
    app.after(100, process_preview_queue)

def process_preview_queue():
    """Process preview updates from queue"""
    global is_processing
    
    if preview_queue.empty() or is_processing:
        return
    
    # Clear queue
    while not preview_queue.empty():
        preview_queue.get()
    
    is_processing = True
    
    try:
        if single_img:
            adj = get_current_adjustments()
            
            # Create thumbnail for faster preview
            max_preview = 1920
            if single_img.width > max_preview or single_img.height > max_preview:
                thumb = single_img.copy()
                thumb.thumbnail((max_preview, max_preview), Image.LANCZOS)
            else:
                thumb = single_img
            
            processed = apply_adjustments(
                thumb,
                adj['brightness'],
                adj['contrast'],
                adj['saturation'],
                adj['sharpness']
            )
            
            viewer.load(processed)
    except Exception as e:
        print(f"Preview error: {e}")
    finally:
        is_processing = False

# ================= SINGLE IMAGE ================= #

def select_image():
    global single_img, single_path
    try:
        p = filedialog.askopenfilename(
            filetypes=[("Images", " ".join(f"*{ext}" for ext in SUPPORTED_EXT))]
        )
        if p:
            single_path = p
            single_img = Image.open(p)
            
            # Reset sliders
            reset_adjustments()
            
            viewer.load(single_img)
            status_label.configure(text=f"Loaded: {os.path.basename(p)} ({single_img.width}x{single_img.height})")
    except Exception as e:
        status_label.configure(text=f"Error loading image: {str(e)}")

def save_single():
    if not single_img:
        status_label.configure(text="No image loaded!")
        return
    
    try:
        # Get adjustments
        adj = get_current_adjustments()
        
        # Apply adjustments
        processed = apply_adjustments(
            single_img,
            adj['brightness'],
            adj['contrast'],
            adj['saturation'],
            adj['sharpness']
        )
        
        # Resize
        size = get_resize_size(processed)
        if size != processed.size:
            processed = processed.resize(size, Image.LANCZOS)

        # Get format and extension
        fmt = format_var.get()
        ext = fmt.lower()
        if ext == "jpg":
            ext = "jpeg"
        
        base = os.path.splitext(os.path.basename(single_path))[0]

        path = filedialog.asksaveasfilename(
            initialfile=f"{config['prefix']}{base}.{ext}",
            defaultextension=f".{ext}",
            filetypes=[(fmt, f"*.{ext}")]
        )
        
        if path:
            # Save with proper format handling
            if fmt == "JPG":
                processed = processed.convert('RGB')
                processed.save(path, "JPEG", quality=95)
            else:
                processed.save(path, fmt)
            
            status_label.configure(text=f"Saved: {os.path.basename(path)}")
    except Exception as e:
        status_label.configure(text=f"Error saving: {str(e)}")
        traceback.print_exc()

# ================= BATCH ================= #

def select_input_folder():
    global input_folder
    folder = filedialog.askdirectory()
    if folder:
        input_folder = folder
        status_label.configure(text=f"Input: {folder}")

def select_output_folder():
    global output_folder
    folder = filedialog.askdirectory()
    if folder:
        output_folder = folder
        status_label.configure(text=f"Output: {folder}")

def batch_convert():
    if not input_folder or not output_folder:
        status_label.configure(text="Select input and output folders!")
        return
    
    def process():
        try:
            files = [f for f in os.listdir(input_folder) if f.lower().endswith(SUPPORTED_EXT)]
            
            if not files:
                status_label.configure(text="No supported images found!")
                return
            
            fmt = format_var.get()
            ext = fmt.lower()
            if ext == "jpg":
                ext = "jpeg"
            
            adj = get_current_adjustments()
            
            progress.set(0)
            batch_button.configure(state="disabled")
            
            for i, f in enumerate(files):
                try:
                    img_path = os.path.join(input_folder, f)
                    img = Image.open(img_path)
                    
                    # Apply adjustments
                    processed = apply_adjustments(
                        img,
                        adj['brightness'],
                        adj['contrast'],
                        adj['saturation'],
                        adj['sharpness']
                    )
                    
                    # Resize
                    size = get_resize_size(processed)
                    if size != processed.size:
                        processed = processed.resize(size, Image.LANCZOS)
                    
                    # Save
                    name = os.path.splitext(f)[0]
                    out_path = os.path.join(output_folder, f"{config['prefix']}{name}.{ext}")
                    
                    if fmt == "JPG":
                        processed = processed.convert('RGB')
                        processed.save(out_path, "JPEG", quality=95)
                    else:
                        processed.save(out_path, fmt)
                    
                    progress.set((i + 1) / len(files))
                    status_label.configure(text=f"Processing: {i+1}/{len(files)} - {f}")
                    app.update_idletasks()
                    
                except Exception as e:
                    print(f"Error processing {f}: {e}")
                    continue
            
            status_label.configure(text=f"Batch complete! Processed {len(files)} images.")
            batch_button.configure(state="normal")
            
        except Exception as e:
            status_label.configure(text=f"Batch error: {str(e)}")
            batch_button.configure(state="normal")
            traceback.print_exc()
    
    # Run in thread to prevent UI freeze
    Thread(target=process, daemon=True).start()

# ================= ADJUSTMENT CONTROLS ================= #

def reset_adjustments():
    """Reset all adjustment sliders to default"""
    brightness_slider.set(1.0)
    contrast_slider.set(1.0)
    saturation_slider.set(1.0)
    sharpness_slider.set(1.0)
    update_preview()

def on_slider_change(value):
    """Called when any slider changes"""
    update_preview()

# ================= UI LAYOUT ================= #

# Left panel - Controls
left = ctk.CTkScrollableFrame(app, width=380)
left.pack(side="left", fill="y", padx=10, pady=10)
left.pack_propagate(False)

# Right panel - Image viewer
right = ctk.CTkFrame(app)
right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

viewer = ImageViewer(right)

# === SINGLE IMAGE SECTION ===
ctk.CTkLabel(left, text="📸 Single Image", font=("", 16, "bold")).pack(pady=(10, 5))

ctk.CTkButton(left, text="Select Image", command=select_image, height=35).pack(pady=6)

# === SIZE CONTROLS ===
ctk.CTkLabel(left, text="📐 Resize", font=("", 14, "bold")).pack(pady=(15, 5))

width_entry = ctk.CTkEntry(left, placeholder_text="Width (blank = original)")
width_entry.pack(pady=4, padx=10, fill="x")

height_entry = ctk.CTkEntry(left, placeholder_text="Height (blank = original)")
height_entry.pack(pady=4, padx=10, fill="x")

keep_ratio = ctk.BooleanVar(value=config["keep_ratio"])
ctk.CTkCheckBox(left, text="🔒 Keep Aspect Ratio", variable=keep_ratio).pack(pady=4)

ctk.CTkLabel(left, text="Presets:").pack(pady=(8, 2))
ctk.CTkOptionMenu(
    left, values=list(PRESETS.keys()),
    command=lambda c: (
        width_entry.delete(0, "end"),
        height_entry.delete(0, "end"),
        width_entry.insert(0, PRESETS[c][0]),
        height_entry.insert(0, PRESETS[c][1])
    )
).pack(pady=4, padx=10, fill="x")

# === FORMAT ===
ctk.CTkLabel(left, text="Format:").pack(pady=(8, 2))
format_var = ctk.StringVar(value=config["format"])
ctk.CTkOptionMenu(left, values=["PNG", "JPG", "WEBP"], variable=format_var).pack(pady=4, padx=10, fill="x")

# === COLOR ADJUSTMENTS ===
ctk.CTkLabel(left, text="🎨 Color Adjustments", font=("", 14, "bold")).pack(pady=(15, 5))

# Brightness
ctk.CTkLabel(left, text="☀️ Brightness").pack(pady=(8, 2))
brightness_slider = ctk.CTkSlider(left, from_=0.2, to=2.0, number_of_steps=180, command=on_slider_change)
brightness_slider.set(config.get("brightness", 1.0))
brightness_slider.pack(pady=4, padx=10, fill="x")

# Contrast
ctk.CTkLabel(left, text="◐ Contrast").pack(pady=(8, 2))
contrast_slider = ctk.CTkSlider(left, from_=0.2, to=2.0, number_of_steps=180, command=on_slider_change)
contrast_slider.set(config.get("contrast", 1.0))
contrast_slider.pack(pady=4, padx=10, fill="x")

# Saturation
ctk.CTkLabel(left, text="🌈 Saturation").pack(pady=(8, 2))
saturation_slider = ctk.CTkSlider(left, from_=0.0, to=2.0, number_of_steps=200, command=on_slider_change)
saturation_slider.set(config.get("saturation", 1.0))
saturation_slider.pack(pady=4, padx=10, fill="x")

# Sharpness
ctk.CTkLabel(left, text="🔍 Sharpness").pack(pady=(8, 2))
sharpness_slider = ctk.CTkSlider(left, from_=0.0, to=2.0, number_of_steps=200, command=on_slider_change)
sharpness_slider.set(config.get("sharpness", 1.0))
sharpness_slider.pack(pady=4, padx=10, fill="x")

ctk.CTkButton(left, text="Reset Adjustments", command=reset_adjustments, fg_color="gray", height=30).pack(pady=8, padx=10, fill="x")

# === SAVE ===
ctk.CTkButton(left, text="💾 Save Single Image", command=save_single, height=40, fg_color="green").pack(pady=10, padx=10, fill="x")

# === BATCH SECTION ===
ctk.CTkLabel(left, text="📦 Batch Processing", font=("", 16, "bold")).pack(pady=(20, 5))

ctk.CTkButton(left, text="Select Input Folder", command=select_input_folder, height=35).pack(pady=4, padx=10, fill="x")
ctk.CTkButton(left, text="Select Output Folder", command=select_output_folder, height=35).pack(pady=4, padx=10, fill="x")

batch_button = ctk.CTkButton(left, text="▶️ Start Batch Convert", command=batch_convert, height=40, fg_color="orange")
batch_button.pack(pady=10, padx=10, fill="x")

progress = ctk.CTkProgressBar(left)
progress.pack(pady=4, padx=10, fill="x")
progress.set(0)

# === STATUS BAR ===
status_label = ctk.CTkLabel(left, text="Ready", wraplength=350)
status_label.pack(pady=10, padx=10)

# === CLEANUP ===
def on_closing():
    """Save config on exit"""
    try:
        config["brightness"] = brightness_slider.get()
        config["contrast"] = contrast_slider.get()
        config["saturation"] = saturation_slider.get()
        config["sharpness"] = sharpness_slider.get()
        config["keep_ratio"] = keep_ratio.get()
        config["format"] = format_var.get()
        save_config(config)
    except:
        pass
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

# Start app
app.mainloop()
