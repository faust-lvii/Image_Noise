import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import customtkinter as ctk
from customtkinter import filedialog
import io
import logging
from typing import Dict, Optional
import gc
from tkinter import messagebox

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_editor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ImageEditor(ctk.CTkToplevel):
    """
    Image Editor application for applying various effects and filters to images.
    Supports multiple image formats and provides real-time preview of effects.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("Image_Noise")
        
        # Initialize image variables with type hints
        self.image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.display_photo: Optional[ctk.CTkImage] = None
        
        # Define supported formats with proper MIME types
        self.supported_formats: Dict[str, str] = {
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
        
        # Initialize settings with default values
        self.current_settings: Dict[str, float] = {
            'noise': 0.0,
            'transparency': 0.0,
            'contrast': 0.0,
            'sharpness': 0.0,
            'brightness': 0.0,
            'saturation': 0.0
        }
        
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Initialize and configure the user interface"""
        self.title("Image Noise Editor")
        self.geometry("1200x800")
        self.minsize(800, 600)

        # Configure main window grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar
        self._setup_sidebar()

        # Create main content area
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Create image display frame with border
        self.image_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.image_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)

        # Create image label
        self.image_label = ctk.CTkLabel(self.image_frame, text="No image loaded", corner_radius=10)
        self.image_label.grid(row=0, column=0, sticky="nsew")

        # Create controls frame at the bottom
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self._setup_controls()

    def _setup_sidebar(self):
        """Setup the sidebar with logo and buttons"""
        # Create sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        # Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Image Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Buttons
        button_params = [
            ("Open Image", self.open_image),
            ("Save Image", self.save_image),
            ("Reset Effects", self.reset_effects)
        ]

        for idx, (text, command) in enumerate(button_params, 1):
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=text,
                command=command,
                width=160,
                height=40,
                corner_radius=8,
                hover_color=("gray70", "gray30")
            )
            btn.grid(row=idx, column=0, padx=20, pady=10)

    def _setup_controls(self):
        """Setup the control panel with sliders"""
        slider_params = [
            ("noise", "Noise"),
            ("contrast", "Contrast"),
            ("brightness", "Brightness"),
            ("saturation", "Saturation"),
            ("sharpness", "Sharpness")
        ]

        self.sliders = {}
        for idx, (param, label) in enumerate(slider_params):
            # Create frame for each control
            control_frame = ctk.CTkFrame(self.controls_frame)
            control_frame.grid(row=0, column=idx, padx=10, pady=5, sticky="ew")
            control_frame.grid_columnconfigure(1, weight=1)

            # Label
            ctk.CTkLabel(control_frame, text=label).grid(row=0, column=0, padx=5)

            # Slider
            slider = ctk.CTkSlider(
                control_frame,
                from_=-100,
                to=100,
                number_of_steps=200,
                command=lambda value, p=param: self.update_image(p, value),
                width=120
            )
            slider.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            slider.set(0)
            self.sliders[param] = slider

    def open_image(self):
        """Open and load an image file"""
        try:
            file_types = [("Image files", 
                        " ".join(f"*{ext}" for exts in self.supported_formats.values() for ext in exts.split()))]
            filename = filedialog.askopenfilename(filetypes=file_types)
            
            if filename:
                self.logger.info(f"Opening image: {filename}")
                self.original_image = Image.open(filename)
                self.image = self.original_image.copy()
                self.logger.info(f"Loaded image size: {self.image.size}, format: {self.image.format}, mode: {self.image.mode}")
                self.update_image_display()
                self.reset_effects()  # Reset all sliders
        except Exception as e:
            self.logger.error(f"Error opening image: {str(e)}")
            self.show_error(f"Error opening image: {str(e)}")
            
    def save_image(self):
        """Save the processed image"""
        if not self.image:
            self.show_error("No image to save")
            return
            
        try:
            file_types = [
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
            filename = filedialog.asksaveasfilename(
                filetypes=file_types,
                defaultextension=".png"
            )
            
            if filename:
                self.logger.info(f"Saving image to: {filename}")
                self.image.save(filename)
        except Exception as e:
            self.logger.error(f"Error saving image: {str(e)}")
            self.show_error(f"Error saving image: {str(e)}")
            
    def update_image(self, param: str, value: float):
        """Update image with new effect parameters"""
        if self.original_image is None:
            return
            
        try:
            self.current_settings[param] = float(value)
            self.apply_effects()
            self.update_image_display()
        except Exception as e:
            self.logger.error(f"Error updating image: {str(e)}")
            self.show_error("Error applying effects")
            
    def apply_effects(self):
        """Apply all effects to the image"""
        if self.original_image is None:
            return
            
        try:
            # Start with a fresh copy of the original image
            self.image = self.original_image.copy()
            
            # Apply effects in optimal order
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
                self._apply_noise()
                
        except Exception as e:
            self.logger.error(f"Error applying effects: {str(e)}")
            self.show_error("Error applying effects")
            
    def _apply_noise(self):
        """Apply noise effect to the image"""
        try:
            img_array = np.array(self.image)
            noise = np.random.normal(0, abs(self.current_settings['noise']), img_array.shape)
            noisy_img = img_array + noise
            noisy_img = np.clip(noisy_img, 0, 255).astype(np.uint8)
            self.image = Image.fromarray(noisy_img)
        except Exception as e:
            self.logger.error(f"Error applying noise: {str(e)}")
            raise
            
    def update_image_display(self):
        """Update the display with the current image"""
        if not self.image:
            self.logger.warning("No image to display.")
            return

        try:
            # Calculate display size while maintaining aspect ratio
            frame_width = self.image_frame.winfo_width() - 20  # Padding
            frame_height = self.image_frame.winfo_height() - 20  # Padding

            if frame_width <= 1 or frame_height <= 1:  # Window not properly sized yet
                frame_width = 800
                frame_height = 600

            # Get original image size
            img_width, img_height = self.image.size

            # Calculate aspect ratios
            width_ratio = frame_width / img_width
            height_ratio = frame_height / img_height

            # Use the smaller ratio to ensure image fits within bounds
            scale_factor = min(width_ratio, height_ratio)

            # Calculate new dimensions
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)

            # Create a copy and resize
            display_image = self.image.copy()
            display_image = display_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to RGB mode
            if display_image.mode != 'RGB':
                display_image = display_image.convert('RGB')

            # Clean up old photo if exists
            if hasattr(self, 'display_photo') and self.display_photo:
                del self.display_photo
                gc.collect()

            # Create new CTkImage
            self.display_photo = ctk.CTkImage(
                light_image=display_image,
                dark_image=display_image,
                size=(new_width, new_height)
            )

            # Update label
            if self.image_label:
                self.image_label.configure(image=self.display_photo, text="")
                self.logger.info(f"Image displayed successfully: {new_width}x{new_height}")

            # Clean up
            del display_image
            gc.collect()

        except Exception as e:
            self.logger.error(f"Error updating display: {str(e)}")
            self.show_error(f"Error updating display: {str(e)}")
            
    def reset_effects(self):
        """Reset all effects to their default values"""
        try:
            for param, slider in self.sliders.items():
                slider.set(0)
                self.current_settings[param] = 0
                
            if self.original_image:
                self.image = self.original_image.copy()
                self.update_image_display()
        except Exception as e:
            self.logger.error(f"Error resetting effects: {str(e)}")
            self.show_error("Error resetting effects")
            
    def show_error(self, message: str):
        """Display error message to user"""
        messagebox.showerror("Error", message)

    def on_closing(self):
        """Clean up resources before closing"""
        try:
            # Clean up resources
            if hasattr(self, 'image_label'):
                self.image_label.configure(image='')
            
            if hasattr(self, 'display_photo'):
                del self.display_photo
            
            self.image = None
            self.original_image = None
            gc.collect()
            
            self.logger.info("Closing Image Editor")
            self.destroy()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            self.destroy()

if __name__ == "__main__":
    try:
        app = ImageEditor()
        app.mainloop()
    except Exception as e:
        logging.error(f"Application crashed: {str(e)}", exc_info=True)
        sys.exit(1)