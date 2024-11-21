import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import customtkinter as ctk
from customtkinter import filedialog
import io

class ImageEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Image Noise Editor")
        self.geometry("1200x800")
        
        # Variables
        self.image = None
        self.original_image = None
        self.supported_formats = {
            "PNG": "*.png",
            "JPEG": "*.jpg *.jpeg *.jpe *.jfif",
            "BMP": "*.bmp",
            "GIF": "*.gif",
            "TIFF": "*.tiff *.tif",
            "WebP": "*.webp",
            "ICO": "*.ico",
            "PPM": "*.ppm",
            "PGM": "*.pgm",
            "HEIC": "*.heic",
            "SVG": "*.svg"
        }
        self.current_settings = {
            'noise': 0,
            'transparency': 0,
            'contrast': 0,
            'sharpness': 0,
            'brightness': 0,
            'saturation': 0
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        # Logo label
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Image Editor", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Buttons
        self.open_button = ctk.CTkButton(self.sidebar_frame, text="Open Image", command=self.open_image)
        self.open_button.grid(row=1, column=0, padx=20, pady=10)
        
        self.save_button = ctk.CTkButton(self.sidebar_frame, text="Save Image", command=self.save_image)
        self.save_button.grid(row=2, column=0, padx=20, pady=10)
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Image display label
        self.image_label = ctk.CTkLabel(self.main_frame, text="No image loaded")
        self.image_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Controls frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")
        
        # Sliders
        self.sliders = {}
        slider_params = [
            ("noise", "Noise"),
            ("transparency", "Transparency"),
            ("contrast", "Contrast"),
            ("sharpness", "Sharpness"),
            ("brightness", "Brightness"),
            ("saturation", "Saturation")
        ]
        
        for i, (param, label) in enumerate(slider_params):
            slider_frame = ctk.CTkFrame(self.controls_frame)
            slider_frame.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
            
            label = ctk.CTkLabel(slider_frame, text=label)
            label.grid(row=0, column=0, padx=10)
            
            slider = ctk.CTkSlider(slider_frame, from_=-100, to=100, number_of_steps=200,
                                 command=lambda value, param=param: self.update_image(param, value))
            slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
            slider.set(0)
            self.sliders[param] = slider
            
    def open_image(self):
        file_types = [("Image files", 
                      " ".join(f"*{ext}" for exts in self.supported_formats.values() for ext in exts.split()))]
        filename = filedialog.askopenfilename(filetypes=file_types)
        
        if filename:
            try:
                self.original_image = Image.open(filename)
                self.image = self.original_image.copy()
                self.update_image_display()
            except Exception as e:
                self.show_error(f"Error opening image: {str(e)}")
                
    def save_image(self):
        if self.image:
            file_types = [("PNG files", "*.png"),
                         ("JPEG files", "*.jpg"),
                         ("All files", "*.*")]
            filename = filedialog.asksaveasfilename(filetypes=file_types, defaultextension=".png")
            
            if filename:
                try:
                    self.image.save(filename)
                except Exception as e:
                    self.show_error(f"Error saving image: {str(e)}")
                    
    def update_image(self, param, value):
        if self.original_image is None:
            return
            
        self.current_settings[param] = float(value)
        self.apply_effects()
        self.update_image_display()
        
    def apply_effects(self):
        if self.original_image is None:
            return
            
        # Start with a fresh copy of the original image
        self.image = self.original_image.copy()
        
        # Apply effects based on current settings
        if self.current_settings['brightness'] != 0:
            enhancer = ImageEnhance.Brightness(self.image)
            self.image = enhancer.enhance(1 + self.current_settings['brightness'] / 100)
            
        if self.current_settings['contrast'] != 0:
            enhancer = ImageEnhance.Contrast(self.image)
            self.image = enhancer.enhance(1 + self.current_settings['contrast'] / 100)
            
        if self.current_settings['saturation'] != 0:
            enhancer = ImageEnhance.Color(self.image)
            self.image = enhancer.enhance(1 + self.current_settings['saturation'] / 100)
            
        if self.current_settings['sharpness'] != 0:
            enhancer = ImageEnhance.Sharpness(self.image)
            self.image = enhancer.enhance(1 + self.current_settings['sharpness'] / 100)
            
        # Apply noise if needed
        if self.current_settings['noise'] != 0:
            img_array = np.array(self.image)
            noise = np.random.normal(0, self.current_settings['noise'], img_array.shape)
            noisy_img = img_array + noise
            noisy_img = np.clip(noisy_img, 0, 255).astype(np.uint8)
            self.image = Image.fromarray(noisy_img)
            
    def update_image_display(self):
        if self.image:
            # Resize image to fit the window while maintaining aspect ratio
            display_size = (800, 600)
            display_image = self.image.copy()
            display_image.thumbnail(display_size, Image.LANCZOS)
            
            # Convert to PhotoImage
            photo = ctk.CTkImage(display_image, size=display_image.size)
            self.image_label.configure(image=photo, text="")
            self.image_label.image = photo
            
    def show_error(self, message):
        ctk.CTkMessagebox(title="Error", message=message, icon="cancel")

if __name__ == "__main__":
    app = ImageEditor()
    app.mainloop()