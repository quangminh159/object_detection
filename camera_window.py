import sys
import cv2
import torch
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTextEdit, QPushButton, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from PyQt5 import uic

class CameraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('mocam.ui', self)
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
        self.cap = None
        self.timer = None
        self.button_start = self.findChild(QPushButton, 'pushButton')
        self.button_stop = self.findChild(QPushButton, 'pushButton_stop')
        self.button_start.clicked.connect(self.start_camera)
        self.button_stop.clicked.connect(self.stop_camera)
        self.label = self.findChild(QLabel, 'label_2')
        self.textEdit = self.findChild(QTextEdit, 'textEdit')
        self.previous_objects = set()
        self.lost_object_counters = {}  

    def show_message(self, title, message, icon=QMessageBox.Information):
        """Hiển thị thông báo."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec_()

    def start_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.show_message("Lỗi", "Không thể mở camera!", QMessageBox.Critical)
                return
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Định dạng video
            self.video_writer = cv2.VideoWriter('output_video.avi', fourcc, 20.0, (640, 480))
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(200)
            self.show_message("Thông báo", "Camera đã được mở.")
        else:
            self.show_message("Thông báo", "Camera đã được mở từ trước.")

    def stop_camera(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            self.cap = None
            if self.timer:
                self.timer.stop()
                self.timer = None
            self.label.clear()
            self.textEdit.clear()
            self.show_message("Thông báo", "Camera đã tắt.")
        else:
            self.show_message("Cảnh báo", "Camera chưa được mở!", QMessageBox.Warning)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
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
        lost_objects = self.previous_objects - detected_objects
        # person_detected = any('person' in obj for obj in detected_objects)
        for obj in lost_objects:
            if obj not in self.lost_object_counters:
                self.lost_object_counters[obj] = 1
            else:
                self.lost_object_counters[obj] += 1
            if self.lost_object_counters[obj] > 5: 
                self.show_warning(f"Đối tượng bị mất: {obj}")
                del self.lost_object_counters[obj]  
        self.previous_objects = detected_objects
        # chỉ thông báo khi phát hiện đối tượng person
        # if any('person' in obj for obj in lost_objects):
        #     # Track and show warning if 'person' is lost for 5 frames
        #     if 'person' not in self.lost_object_counters:
        #         self.lost_object_counters['person'] = 1
        #     else:
        #         self.lost_object_counters['person'] += 1
        #     if self.lost_object_counters['person'] > 5: 
        #         self.show_warning("Đối tượng 'person' bị mất!")
        #         del self.lost_object_counters['person']  
        # else:
        #     if 'person' in detected_objects:
        #         self.lost_object_counters['person'] = 0

        height, width, channels = rgb_frame.shape
        bytes_per_line = 3 * width
        qimage = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.label.setPixmap(pixmap.scaled(self.label.size(), aspectRatioMode=1))
        self.label.setScaledContents(True)

    def show_warning(self, message):
        current_text = self.textEdit.toPlainText()
        self.textEdit.setText(current_text + "\n" + message)
        self.textEdit.moveCursor(self.textEdit.textCursor().End)  

    def closeEvent(self, event):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraWindow()
    window.show()
    sys.exit(app.exec_())
