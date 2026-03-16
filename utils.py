#utils.py
from PyQt6.QtGui import QImage, QPixmap
import cv2

def cv2_to_qpixmap(cv_img):
    rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qt_img = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qt_img)