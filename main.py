# main_window.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5 import uic
from camera_window import CameraWindow
from video_window import VideoWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('trangchu.ui', self)  
        self.pushButton.clicked.connect(self.open_camera_window)
        self.pushButton_2.clicked.connect(self.open_video_window)

    def open_camera_window(self):
        self.camera_window = CameraWindow()  
        self.camera_window.show() 

    def open_video_window(self):
        self.video_window = VideoWindow()  
        self.video_window.show() 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()  
    window.show()  
    sys.exit(app.exec_())  