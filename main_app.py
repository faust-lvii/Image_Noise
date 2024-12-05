import customtkinter as ctk
from Image_Noise import ImageEditor
from Video_Editor import VideoEditor  # VideoEditor sınıfını içe aktar
import logging
import sys
from tkinter import messagebox

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('media_editor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class MainApplication(ctk.CTk):
    """
    Main application window that serves as a launcher for Image and Video editors.
    Provides a clean interface to switch between different editing tools.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_window()
        self.create_ui()
        
    def setup_window(self):
        """Configure main window properties and geometry"""
        self.title("Media Editor")
        self.geometry("1200x800")
        self.minsize(800, 600)  # Set minimum window size
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_ui(self):
        """Create and setup all UI elements"""
        # Create header frame
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Create buttons with hover effects
        self.image_button = ctk.CTkButton(
            self.header_frame, 
            text="Image Editor", 
            command=self.open_image_editor,
            hover_color=("gray70", "gray30")
        )
        self.image_button.pack(side="left", padx=10)
        
        # Activate VideoEditor button
        self.video_button = ctk.CTkButton(
            self.header_frame, 
            text="Video Editor", 
            command=self.open_video_editor,
            hover_color=("gray70", "gray30")
        )
        self.video_button.pack(side="left", padx=10)
        
        # Content frame for editors
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        self.current_editor = None
        
    def open_image_editor(self):
        """Open the image editor window and handle any errors"""
        try:
            self.safely_close_current_editor()
            self.logger.info("Opening Image Editor")
            self.current_editor = ImageEditor(self)
            self.current_editor.attributes('-topmost', True)
            self.current_editor.focus()
        except Exception as e:
            self.logger.error(f"Error opening Image Editor: {str(e)}")
            self.show_error("Failed to open Image Editor")
            
    def open_video_editor(self):
        """Open the video editor window and handle any errors"""
        try:
            self.safely_close_current_editor()
            self.logger.info("Opening Video Editor")
            self.current_editor = VideoEditor(self)
            self.current_editor.attributes('-topmost', True)
            self.current_editor.focus()
        except Exception as e:
            self.logger.error(f"Error opening Video Editor: {str(e)}")
            self.show_error("Failed to open Video Editor")
            
    def safely_close_current_editor(self):
        """Safely close the current editor if one exists"""
        if self.current_editor and self.current_editor.winfo_exists():
            self.current_editor.destroy()
        self.current_editor = None
        
    def show_error(self, message):
        """Display error message to user"""
        messagebox.showerror("Error", message)
        
    def on_closing(self):
        """Handle application shutdown"""
        self.safely_close_current_editor()
        self.logger.info("Shutting down application")
        self.quit()

if __name__ == "__main__":
    try:
        app = MainApplication()
        app.mainloop()
    except Exception as e:
        logging.error(f"Application crashed: {str(e)}", exc_info=True)
        sys.exit(1)
