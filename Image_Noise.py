import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import customtkinter as ctk
from customtkinter import filedialog
import io
import logging
from typing import Dict, Optional, Tuple
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

class ImageEditor(ctk.CTk):
    """
    Image Editor application for applying various effects and filters to images.
    Supports multiple image formats and provides real-time preview of effects.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
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
        # Configure window
        self.title("Image Noise Editor")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._setup_sidebar()
        self._setup_main_area()
        self._setup_controls()
        
    def _setup_sidebar(self):
        """Setup the sidebar with logo and buttons"""
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        # Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Image Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Buttons
        self.open_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Open Image",
            command=self.open_image,
            hover_color=("gray70", "gray30")
        )
        self.open_button.grid(row=1, column=0, padx=20, pady=10)
        
        self.save_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Save Image",
            command=self.save_image,
            hover_color=("gray70", "gray30")
        )
        self.save_button.grid(row=2, column=0, padx=20, pady=10)
        
        # Reset button
        self.reset_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Reset Effects",
            command=self.reset_effects,
            hover_color=("gray70", "gray30")
        )
        self.reset_button.grid(row=3, column=0, padx=20, pady=10)
        
    def _setup_main_area(self):
        """Setup the main content area"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.image_label = ctk.CTkLabel(self.main_frame, text="No image loaded")
        self.image_label.grid(row=0, column=0, padx=20, pady=20)
        
    def _setup_controls(self):
        """Setup the control panel with sliders"""
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")
        
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
            
            slider = ctk.CTkSlider(
                slider_frame,
                from_=-100,
                to=100,
                number_of_steps=200,
                command=lambda value, param=param: self.update_image(param, value)
            )
            slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
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
            # Resize image to fit the window while maintaining aspect ratio
            display_size = (800, 600)
            display_image = self.image.copy()
            
            # Log the original size and mode of the image
            self.logger.info(f"Original image size: {self.image.size}, mode: {self.image.mode}")
            
            display_image.thumbnail(display_size, Image.LANCZOS)
            
            # Log the new size of the image after thumbnail
            self.logger.info(f"Thumbnail image size: {display_image.size}, mode: {display_image.mode}")
            
            # Convert to a format compatible with CTkImage
            self.display_photo = ctk.CTkImage(display_image.convert("RGBA"))
            
            # Log the display photo creation
            self.logger.info("CTkImage created successfully.")
            
            # Update display
            if self.image_label is not None:
                self.image_label.configure(image=self.display_photo, text="")
                self.logger.info("Image label updated successfully.")
            else:
                self.logger.error("Image label is not initialized.")
            
            # Keep a reference to the CTkImage to prevent garbage collection
            self.image_label.image = self.display_photo
            
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
            self.image = None
            self.original_image = None
            self.display_photo = None
            gc.collect()
            
            self.logger.info("Closing Image Editor")
            self.quit()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            self.quit()

    def load_image(self, image_path):
        """Load an image and handle errors"""
        try:
            self.image = Image.open(image_path)  # Example of loading an image
            self.display_image()  # Method to display the image
            self.logger.info(f"Successfully loaded image: {image_path}")
        except FileNotFoundError:
            self.logger.error(f"File not found: {image_path}")
            self.show_error("Image file not found.")
        except Exception as e:
            self.logger.error(f"Error loading image: {str(e)}")
            self.show_error("Failed to load image.")

if __name__ == "__main__":
    try:
        app = ImageEditor()
        app.mainloop()
    except Exception as e:
        logging.error(f"Application crashed: {str(e)}", exc_info=True)
        sys.exit(1)