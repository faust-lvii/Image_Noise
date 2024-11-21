import sys
import cv2
import numpy as np
import customtkinter as ctk
from customtkinter import filedialog
from PIL import Image, ImageTk
from moviepy.editor import VideoFileClip
import tempfile
import os
from threading import Thread

class VideoProcessor(Thread):
    def __init__(self, video_path, settings, callback):
        super().__init__()
        self.video_path = video_path
        self.settings = settings
        self.callback = callback
        self.is_running = True

    def run(self):
        try:
            clip = VideoFileClip(self.video_path)
            frames = []
            total_frames = int(clip.duration * clip.fps)
            
            for i, frame in enumerate(clip.iter_frames()):
                if not self.is_running:
                    break
                    
                # Apply effects
                frame = self.apply_effects(frame)
                frames.append(frame)
                
                # Update progress
                progress = int((i + 1) / total_frames * 100)
                self.callback("progress", progress)
                
            if self.is_running:
                # Save processed video
                temp_file = tempfile.mktemp(suffix='.mp4')
                out_clip = VideoFileClip(self.video_path)
                out_clip.write_videofile(temp_file, 
                                       fps=clip.fps,
                                       codec='libx264',
                                       audio_codec='aac')
                
                self.callback("finished", temp_file)
                
        except Exception as e:
            self.callback("error", str(e))
            
    def apply_effects(self, frame):
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
                
            # Clip values to valid range
            frame = np.clip(frame, 0, 255).astype(np.uint8)
            
            return frame
            
        except Exception as e:
            print(f"Error applying effects: {str(e)}")
            return frame.astype(np.uint8)
            
    def stop(self):
        self.is_running = False

class VideoEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Video Editor")
        self.geometry("1200x800")
        
        self.video_processor = None
        self.current_video_path = None
        self.current_settings = {
            'noise': 0,
            'brightness': 0,
            'contrast': 0
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
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Video Editor", 
                                     font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Buttons
        self.open_button = ctk.CTkButton(self.sidebar_frame, text="Open Video", 
                                       command=self.open_video)
        self.open_button.grid(row=1, column=0, padx=20, pady=10)
        
        self.process_button = ctk.CTkButton(self.sidebar_frame, text="Process Video",
                                          command=self.process_video)
        self.process_button.grid(row=2, column=0, padx=20, pady=10)
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Video preview label
        self.video_label = ctk.CTkLabel(self.main_frame, text="No video loaded")
        self.video_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Controls frame
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
            
            slider = ctk.CTkSlider(slider_frame, from_=-100, to=100, number_of_steps=200,
                                 command=lambda value, param=param: self.update_settings(param, value))
            slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
            slider.set(0)
            self.sliders[param] = slider
            
    def open_video(self):
        file_types = [("Video files", "*.mp4 *.avi *.mov *.mkv")]
        filename = filedialog.askopenfilename(filetypes=file_types)
        
        if filename:
            try:
                self.current_video_path = filename
                # Load first frame for preview
                cap = cv2.VideoCapture(filename)
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    preview = Image.fromarray(frame)
                    preview.thumbnail((800, 600))
                    photo = ctk.CTkImage(preview, size=preview.size)
                    self.video_label.configure(image=photo, text="")
                    self.video_label.image = photo
                cap.release()
            except Exception as e:
                self.show_error(f"Error opening video: {str(e)}")
                
    def process_video(self):
        if not self.current_video_path:
            self.show_error("Please open a video first")
            return
            
        if self.video_processor and self.video_processor.is_alive():
            self.video_processor.stop()
            self.video_processor.join()
            
        self.progress_bar.set(0)
        self.video_processor = VideoProcessor(
            self.current_video_path,
            self.current_settings,
            self.process_callback
        )
        self.video_processor.start()
        
    def process_callback(self, status, data):
        if status == "progress":
            self.progress_bar.set(data / 100)
        elif status == "finished":
            self.show_save_dialog(data)
        elif status == "error":
            self.show_error(data)
            
    def show_save_dialog(self, temp_file):
        file_types = [("MP4 files", "*.mp4")]
        filename = filedialog.asksaveasfilename(filetypes=file_types,
                                              defaultextension=".mp4")
        if filename:
            try:
                os.replace(temp_file, filename)
                self.show_info("Video saved successfully!")
            except Exception as e:
                self.show_error(f"Error saving video: {str(e)}")
                
    def update_settings(self, param, value):
        self.current_settings[param] = float(value)
        
    def show_error(self, message):
        ctk.CTkMessagebox(title="Error", message=message, icon="cancel")
        
    def show_info(self, message):
        ctk.CTkMessagebox(title="Success", message=message, icon="info")
        
    def on_closing(self):
        if self.video_processor and self.video_processor.is_alive():
            self.video_processor.stop()
            self.video_processor.join()
        self.quit()

if __name__ == "__main__":
    app = VideoEditor()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()