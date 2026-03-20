# yolo_detector.py
from ultralytics import YOLO

class YoloDetector:
    def __init__(self, model_path="best.pt"):
        self.model = YOLO(model_path)
        self.names = self.model.names  # class names

    def detect(self, image, conf_threshold=0.25):
        results = self.model(image)[0]

        detections = []

        if results.boxes is None:
            return detections

        for b in results.boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            conf = float(b.conf[0])
            cls_id = int(b.cls[0])

            if conf < conf_threshold:
                continue

            label = self.names.get(cls_id, str(cls_id))

            detections.append({
                "bbox": (x1, y1, x2, y2),
                "conf": conf,
                "class_id": cls_id,
                "label": label
            })

        return detections