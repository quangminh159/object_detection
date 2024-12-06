import sys
import cv2
import torch
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTextEdit, QPushButton, QFileDialog, QMessageBox, QLineEdit
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from PyQt5 import uic

class VideoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('taivideo.ui', self)  
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s') 
        self.cap = None
        self.timer = None
        
        self.button_upload = self.findChild(QPushButton, 'pushButton')  
        self.textEdit = self.findChild(QTextEdit, 'textEdit')  
        self.label_video = self.findChild(QLabel, 'label_2')  
        self.lineEdit = self.findChild(QLineEdit, 'lineEdit')  
        self.button_upload.clicked.connect(self.upload_video)
        
    def upload_video(self):
        """Mở hộp thoại để tải video và xử lý."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Chọn video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_name:
            self.lineEdit.setText(file_name.split('/')[-1])  
            self.process_video(file_name)  
    def process_video(self, file_path):
        """Xử lý video và nhận diện đối tượng."""
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            self.show_message("Lỗi", "Không thể mở video!", QMessageBox.Critical)
            return
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame) 
        self.timer.start(30)

    def update_frame(self):
        """Cập nhật và xử lý từng frame của video."""
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.show_message("Thông báo", "Video đã kết thúc!")
            return
        
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model(rgb_frame)  
        detected_objects = set()
        if results.xyxy[0].shape[0] > 0: 
            for *xyxy, conf, cls in results.xyxy[0]:
                label = self.model.names[int(cls)]
                confidence = conf.item()
                if confidence > 0.5:
                    x1, y1, x2, y2 = map(int, xyxy)
                    cv2.rectangle(rgb_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(rgb_frame, f'{label} {confidence:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    detected_objects.add(f'{label} {confidence:.2f}')
        else:
            detected_objects.add("Không phát hiện đối tượng nào.")
        self.textEdit.setText("\n".join(detected_objects))
        height, width, channels = rgb_frame.shape
        bytes_per_line = 3 * width
        qimage = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.label_video.setPixmap(pixmap.scaled(self.label_video.size(), aspectRatioMode=1))
        self.label_video.setScaledContents(True)

    def show_message(self, title, message, icon=QMessageBox.Information):
        """Hiển thị thông báo."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec_()

    def closeEvent(self, event):
        """Giải phóng tài nguyên khi đóng cửa sổ."""
        if self.cap and self.cap.isOpened():
            self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoWindow()
    window.show()
    sys.exit(app.exec_())
