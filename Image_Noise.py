import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QSlider, QLabel,
                             QHBoxLayout, QProgressBar, QStyle, QStyleFactory)
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer

class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.image = None
        self.original_image = None
        self.current_settings = {'noise': 0, 'transparency': 0}

    def initUI(self):
        self.setWindowTitle('Image Editor')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Open and Save buttons
        button_layout = QHBoxLayout()
        self.open_button = QPushButton('Open Image', self)
        self.open_button.clicked.connect(self.open_image)
        button_layout.addWidget(self.open_button)

        self.save_button = QPushButton('Save Image', self)
        self.save_button.clicked.connect(self.save_image)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        # Noise effect controls
        noise_layout = QHBoxLayout()
        self.noise_slider = QSlider(Qt.Horizontal)
        self.noise_slider.setRange(0, 100)
        self.noise_slider.valueChanged.connect(self.apply_effects)
        noise_layout.addWidget(QLabel('Noise Level:'))
        noise_layout.addWidget(self.noise_slider)
        layout.addLayout(noise_layout)

        # Transparency controls
        transparency_layout = QHBoxLayout()
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setRange(0, 100)
        self.transparency_slider.valueChanged.connect(self.apply_effects)
        transparency_layout.addWidget(QLabel('Transparency:'))
        transparency_layout.addWidget(self.transparency_slider)
        layout.addLayout(transparency_layout)

        # Image display
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.apply_dark_theme()

    def apply_dark_theme(self):
        app = QApplication.instance()
        app.setStyle(QStyleFactory.create("Fusion"))
        
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        app.setPalette(dark_palette)
        
        app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    def open_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_name:
            self.original_image = cv2.imread(file_name)
            self.image = self.original_image.copy()
            self.current_settings = {'noise': 0, 'transparency': 0}
            self.noise_slider.setValue(0)
            self.transparency_slider.setValue(0)
            self.display_image(self.image)

    def apply_effects(self):
        if self.original_image is not None:
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            # Update current settings
            self.current_settings['noise'] = self.noise_slider.value()
            self.current_settings['transparency'] = self.transparency_slider.value()

            # Apply noise
            noise_level = self.current_settings['noise'] / 100.0
            noise = np.random.normal(0, noise_level * 255, self.original_image.shape).astype(np.uint8)
            noisy_img = cv2.add(self.original_image, noise)

            # Apply transparency
            transparency = self.current_settings['transparency'] / 100.0
            self.image = cv2.addWeighted(self.original_image, 1 - transparency, noisy_img, transparency, 0)

            self.display_image(self.image)
            
            # Simulate processing time
            for i in range(101):
                self.progress_bar.setValue(i)
                QApplication.processEvents()
                QTimer.singleShot(10, lambda: None)

    def save_image(self):
        if self.image is not None:
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)")
            if file_name:
                cv2.imwrite(file_name, self.image)

    def display_image(self, img):
        height, width, channel = img.shape
        bytes_per_line = 3 * width
        q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        
        # Scale pixmap to fit the label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = ImageEditor()
    editor.show()
    sys.exit(app.exec_())