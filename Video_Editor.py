import sys
import cv2
import numpy as np
import customtkinter as ctk
from customtkinter import filedialog
from PIL import Image, ImageTk
import tempfile
import os
from threading import Thread, Event
import logging
from typing import Dict, Optional, Tuple, Callable
import gc
from tkinter import messagebox

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_editor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class VideoProcessor(Thread):
    """Thread class for processing video files with effects"""
    
    def __init__(self, video_path: str, settings: Dict[str, float], callback: Callable):
        super().__init__()
        self.video_path = video_path
        self.settings = settings
        self.callback = callback
        self.is_running = True
        self.stop_event = Event()
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Main processing loop for video effects"""
        try:
            # Open input video
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
                
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Create output video file
            temp_file = tempfile.mktemp(suffix='.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_file, fourcc, fps, (width, height))
            
            frame_count = 0
            
            while cap.isOpened():
                if self.stop_event.is_set():
                    self.logger.info("Processing cancelled")
                    break
                    
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Process frame with effects
                processed_frame = self.apply_effects(frame)
                
                # Write processed frame
                out.write(processed_frame)
                
                # Update progress
                frame_count += 1
                progress = int((frame_count / total_frames) * 100)
                self.callback("progress", progress)
                
            # Clean up
            cap.release()
            out.release()
            
            if not self.stop_event.is_set():
                self.logger.info(f"Video processing completed: {temp_file}")
                self.callback("finished", temp_file)
            else:
                # Clean up temp file if processing was cancelled
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            self.logger.error(f"Error processing video: {str(e)}")
            self.callback("error", str(e))
            
    def apply_effects(self, frame: np.ndarray) -> np.ndarray:
        """Apply visual effects to a single frame"""
        try:
            # Convert frame to float32 for calculations
            frame = frame.astype(np.float32)
            
            # Apply effects based on settings
            if self.settings['brightness'] != 0:
                frame = frame * (1.0 + self.settings['brightness'] / 100.0)
                
            if self.settings['contrast'] != 0:
                frame = frame * (1.0 + self.settings['contrast'] / 100.0)
                
            if self.settings['noise'] > 0:
                noise = np.random.normal(0, self.settings['noise'], frame.shape)
                frame = frame + noise
                
            # Clip values to valid range and convert back to uint8
            frame = np.clip(frame, 0, 255).astype(np.uint8)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error applying effects to frame: {str(e)}")
            return frame.astype(np.uint8)
            
    def stop(self):
        """Stop video processing"""
        self.stop_event.set()
        self.is_running = False

class VideoPlayer:
    """Video player component for previewing videos"""
    def __init__(self, parent, width=640, height=480):
        self.parent = parent
        self.width = width
        self.height = height
        self.is_playing = False
        self.current_frame = None
        self.cap = None
        self.logger = logging.getLogger(__name__)
        
        # Create video display canvas
        self.canvas = ctk.CTkCanvas(parent, width=width, height=height, bg='black')
        self.canvas.pack(pady=10)
        
        # Create control buttons
        self.controls_frame = ctk.CTkFrame(parent)
        self.controls_frame.pack(pady=5)
        
        self.play_button = ctk.CTkButton(self.controls_frame, text="Play", command=self.toggle_play)
        self.play_button.pack(side='left', padx=5)
        
        self.stop_button = ctk.CTkButton(self.controls_frame, text="Stop", command=self.stop)
        self.stop_button.pack(side='left', padx=5)
        
    def load_video(self, video_path):
        """Load a video file for playback"""
        if self.cap is not None:
            self.stop()
            
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            self.logger.error(f"Could not open video: {video_path}")
            return False
            
        # Get video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_delay = int(1000 / self.fps)  # Delay in milliseconds
        return True
        
    def toggle_play(self):
        """Toggle video playback"""
        if self.cap is None:
            return
            
        if self.is_playing:
            self.is_playing = False
            self.play_button.configure(text="Play")
        else:
            self.is_playing = True
            self.play_button.configure(text="Pause")
            self.play()
            
    def play(self):
        """Play video frame by frame"""
        if not self.is_playing or self.cap is None:
            return
            
        ret, frame = self.cap.read()
        if ret:
            # Resize frame to fit canvas
            frame = cv2.resize(frame, (self.width, self.height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image=image)
            
            # Update canvas
            self.current_frame = photo
            self.canvas.create_image(0, 0, anchor='nw', image=photo)
            
            # Schedule next frame
            self.parent.after(self.frame_delay, self.play)
        else:
            # Video ended
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.is_playing = False
            self.play_button.configure(text="Play")
            
    def stop(self):
        """Stop video playback"""
        self.is_playing = False
        self.play_button.configure(text="Play")
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        # Clear canvas
        self.canvas.delete("all")
        
    def destroy(self):
        """Clean up resources"""
        self.stop()
        self.canvas.destroy()
        self.controls_frame.destroy()

class VideoEditor(ctk.CTk):
    """Video Editor application for applying effects to video files"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Initialize variables
        self.video_processor: Optional[VideoProcessor] = None
        self.video_player: Optional[VideoPlayer] = None
        self.current_video_path: Optional[str] = None
        self.current_settings: Dict[str, float] = {
            'noise': 0.0,
            'brightness': 0.0,
            'contrast': 0.0
        }
        
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Initialize and configure the user interface"""
        # Window setup
        self.title("Video Editor")
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
            text="Video Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Buttons
        self.open_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Open Video",
            command=self.open_video,
            hover_color=("gray70", "gray30")
        )
        self.open_button.grid(row=1, column=0, padx=20, pady=10)
        
        self.process_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Process Video",
            command=self.process_video,
            hover_color=("gray70", "gray30")
        )
        self.process_button.grid(row=2, column=0, padx=20, pady=10)
        
        # Cancel button (initially disabled)
        self.cancel_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Cancel Processing",
            command=self.cancel_processing,
            state="disabled",
            hover_color=("gray70", "gray30")
        )
        self.cancel_button.grid(row=3, column=0, padx=20, pady=10)
        
    def _setup_main_area(self):
        """Setup the main content area"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Create video player
        self.video_player = VideoPlayer(self.main_frame)

    def _setup_controls(self):
        """Setup the control panel with progress bar and sliders"""
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.controls_frame)
        self.progress_bar.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)
        
        # Sliders
        self.sliders = {}
        slider_params = [
            ("noise", "Noise"),
            ("brightness", "Brightness"),
            ("contrast", "Contrast")
        ]
        
        for i, (param, label) in enumerate(slider_params):
            slider_frame = ctk.CTkFrame(self.controls_frame)
            slider_frame.grid(row=i+1, column=0, padx=10, pady=5, sticky="ew")
            
            label = ctk.CTkLabel(slider_frame, text=label)
            label.grid(row=0, column=0, padx=10)
            
            slider = ctk.CTkSlider(
                slider_frame,
                from_=-100,
                to=100,
                number_of_steps=200,
                command=lambda value, param=param: self.update_settings(param, value)
            )
            slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
            slider.set(0)
            self.sliders[param] = slider
            
    def open_video(self):
        """Open and preview a video file"""
        try:
            file_types = [("Video files", "*.mp4 *.avi *.mov *.mkv")]
            filename = filedialog.askopenfilename(filetypes=file_types)
            
            if filename:
                self.logger.info(f"Opening video: {filename}")
                self.current_video_path = filename
                
                # Load video for preview
                if self.video_player:
                    self.video_player.load_video(filename)
                    
        except Exception as e:
            self.logger.error(f"Error opening video: {str(e)}")
            self.show_error(f"Error opening video: {str(e)}")
            
    def process_video(self):
        """Start video processing in a separate thread"""
        if not self.current_video_path:
            self.show_error("Please open a video first")
            return
            
        try:
            # Cancel any existing processing
            if self.video_processor and self.video_processor.is_alive():
                self.cancel_processing()
                
            self.progress_bar.set(0)
            self.cancel_button.configure(state="normal")
            self.process_button.configure(state="disabled")
            
            self.video_processor = VideoProcessor(
                self.current_video_path,
                self.current_settings,
                self.process_callback
            )
            self.video_processor.start()
            
        except Exception as e:
            self.logger.error(f"Error starting video processing: {str(e)}")
            self.show_error("Error starting video processing")
            
    def cancel_processing(self):
        """Cancel ongoing video processing"""
        if self.video_processor and self.video_processor.is_alive():
            self.logger.info("Cancelling video processing")
            self.video_processor.stop()
            self.video_processor.join()
            self.process_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
            
    def process_callback(self, status: str, data: any):
        """Handle callbacks from video processor"""
        if status == "progress":
            self.progress_bar.set(data / 100)
        elif status == "finished":
            self.progress_bar.set(0)
            self.show_success("Video processing completed!")
            # Load processed video for preview
            if self.video_player:
                self.video_player.load_video(data)
        elif status == "error":
            self.show_error(f"Error processing video: {data}")
            self.progress_bar.set(0)

    def update_settings(self, param: str, value: float):
        """Update effect settings"""
        self.current_settings[param] = float(value)
        
    def show_error(self, message: str):
        """Display error message to user"""
        messagebox.showerror("Error", message)
        
    def show_success(self, message: str):
        """Display success message to user"""
        messagebox.showinfo("Success", message)
        
    def on_closing(self):
        """Clean up resources before closing"""
        try:
            self.cancel_processing()
            self.logger.info("Closing Video Editor")
            self.quit()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            self.quit()

if __name__ == "__main__":
    try:
        app = VideoEditor()
        app.mainloop()
    except Exception as e:
        logging.error(f"Application crashed: {str(e)}", exc_info=True)
        sys.exit(1)