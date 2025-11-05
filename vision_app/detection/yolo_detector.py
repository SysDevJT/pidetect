import cv2
from ultralytics import YOLO
from ..config import Config
import logging

logger = logging.getLogger(__name__)

class YoloDetector:
    """
    Handles object detection using the YOLO model.
    """
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        logger.info(f"YOLO model loaded from {model_path}")

    def detect(self, frame_bgr):
        """
        Performs object detection on a single frame.
        """
        small_frame = cv2.resize(frame_bgr, Config.FRAME_SIZE)
        results = self.model(small_frame, conf=Config.CONF_MIN, classes=[0, 15], verbose=False) # 0=person, 15=cat

        objects = []
        for r in results[0].boxes:
            label = self.model.names[int(r.cls)]
            conf = float(r.conf)
            objects.append({"label": label, "confidence": round(conf, 3)})

        summary = f"Detected {len(objects)} objects: {', '.join(o['label'] for o in objects)}"[:200]
        return {"summary": summary, "objects": objects}
