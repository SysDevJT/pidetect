import cv2
import logging
from .base import VideoStream

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2
    PICAM_AVAILABLE = True
except ImportError:
    PICAM_AVAILABLE = False

class PiCamStream(VideoStream):
    """
    Represents a video stream from a PiCamera.
    """
    def __init__(self):
        if not PICAM_AVAILABLE:
            raise RuntimeError("Picamera2 not available. Please install it.")

        self.picam2 = Picamera2()
        cfg = self.picam2.create_video_configuration(
            main={"size": (1280, 720), "format": "RGB888"}
        )
        self.picam2.configure(cfg)
        self.picam2.start()
        logger.debug("PiCamera stream initialized")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def read(self):
        frame_rgb = self.picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        return frame_bgr

    def release(self):
        if self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
                logger.debug("PiCamera stream released")
            except Exception as e:
                logger.error(f"Error releasing PiCamera stream: {e}")

def is_picam_available():
    return PICAM_AVAILABLE
