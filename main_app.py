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
        self.title("Media Editor Pro")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Siyah-beyaz tema ayarları
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.configure(fg_color=("#ffffff", "#000000"))
        
        # Ana başlık
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(20, 10), fill="x")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Media Editor Pro",
            font=ctk.CTkFont(family="Helvetica", size=32, weight="bold"),
            text_color=("#1a1a1a", "#ffffff")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Professional Media Editing Suite",
            font=ctk.CTkFont(family="Helvetica", size=14),
            text_color=("#4a4a4a", "#b0b0b0")
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_ui(self):
        """Create and setup all UI elements"""
        # Create header frame
        self.header_frame = ctk.CTkFrame(self, bg_color="#2E2E2E")  # Darker header frame
        self.header_frame.pack(padx=10, pady=10, fill="x")
        
        # Create buttons with hover effects
        self.create_buttons()
        
        # Content frame for editors
        self.content_frame = ctk.CTkFrame(self, bg_color="#1E1E1E")  # Dark content frame
        self.content_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        
        self.current_editor = None
        
    def create_buttons(self):
        """Create buttons for image and video editors with modern design"""
        button_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color=("#f0f0f0", "#1a1a1a"),
            corner_radius=15
        )
        button_frame.pack(pady=20, padx=30, fill="x")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Image Editor Button
        self.image_button = ctk.CTkButton(
            button_frame,
            text="Image Editor",
            command=self.open_image_editor,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=("#2a2a2a", "#ffffff"),
            hover_color=("#4a4a4a", "#b0b0b0"),
            text_color=("#ffffff", "#000000"),
            border_spacing=10
        )
        self.image_button.grid(row=0, column=0, padx=20, sticky="ew")
        
        # Video Editor Button
        self.video_button = ctk.CTkButton(
            button_frame,
            text="Video Editor",
            command=self.open_video_editor,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=("#2a2a2a", "#ffffff"),
            hover_color=("#4a4a4a", "#b0b0b0"),
            text_color=("#ffffff", "#000000"),
            border_spacing=10
        )
        self.video_button.grid(row=0, column=1, padx=20, sticky="ew")
        
    def open_image_editor(self):
        """Open the image editor window and handle any errors"""
        try:
            self.safely_close_current_editor()
            self.logger.info("Opening Image Editor")
            
            # Ana pencereyi minimize et
            self.iconify()
            
            # Image Editor'ı oluştur
            self.current_editor = ImageEditor(self)
            
            # Image Editor'ı ana pencere olarak ayarla
            self.current_editor.attributes('-topmost', True)
            self.current_editor.focus_force()
            
            # Image Editor kapatıldığında ana pencereyi geri getir
            def on_editor_close():
                self.current_editor.destroy()
                self.deiconify()
                self.current_editor = None
            
            self.current_editor.protocol("WM_DELETE_WINDOW", on_editor_close)
            
        except Exception as e:
            self.logger.error(f"Error opening Image Editor: {str(e)}", exc_info=True)
            self.show_error("Failed to open Image Editor")
            self.deiconify()  # Hata durumunda ana pencereyi geri getir
            
    def open_video_editor(self):
        """Open the video editor window and handle any errors"""
        try:
            self.safely_close_current_editor()
            self.logger.info("Opening Video Editor")
            self.attributes('-topmost', False)  # Ana pencereyi arka plana al
            self.current_editor = VideoEditor(self)
            self.current_editor.attributes('-topmost', True)  # VideoEditor'ı ön plana al
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
