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
        self.configure(bg="#2E2E2E")  # Set background color

        # Create a title label
        title_label = ctk.CTkLabel(self, text="Media Editor", font=("Arial", 24), text_color="white", bg_color="#2E2E2E")
        title_label.pack(pady=(10, 20))

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_ui(self):
        """Create and setup all UI elements"""
        # Create header frame
        self.header_frame = ctk.CTkFrame(self, bg_color="#3E3E3E")
        self.header_frame.pack(padx=10, pady=10, fill="x")
        
        # Create buttons with hover effects
        self.create_buttons()
        
        # Content frame for editors
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        
        self.current_editor = None
        
    def create_buttons(self):
        """Create buttons for image and video editors"""
        self.image_button = ctk.CTkButton(
            self.header_frame, 
            text="Image Editor", 
            command=self.open_image_editor,
            hover_color=("gray70", "gray30"),
            fg_color="#4CAF50",  # Green color
            text_color="white",
            width=150
        )
        self.image_button.pack(side="left", padx=10)
        
        self.video_button = ctk.CTkButton(
            self.header_frame, 
            text="Video Editor", 
            command=self.open_video_editor,
            hover_color=("gray70", "gray30"),
            fg_color="#2196F3",  # Blue color
            text_color="white",
            width=150
        )
        self.video_button.pack(side="left", padx=10)
        
        # Add a separator for better visual distinction
        separator = ctk.CTkFrame(self.header_frame, height=2, bg_color="white")
        separator.pack(side="left", padx=10, fill="y")
        
        # Add more buttons or features as needed
        
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
