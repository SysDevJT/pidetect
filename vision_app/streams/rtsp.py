import cv2
import logging
import time
from .base import VideoStream
from ..config import Config

logger = logging.getLogger(__name__)

class RTSPStream(VideoStream):
    """
    Represents a video stream from an RTSP source.
    """
    def __init__(self, url):
        self.url = url
        self.cap = None

    def __enter__(self):
        max_attempts = Config.MAX_RECONNECT_ATTEMPTS
        for attempt in range(max_attempts):
            try:
                self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
                if not self.cap.isOpened():
                    raise RuntimeError(f"Cannot open RTSP stream: {self.url}")

                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                # Check if we can read a frame
                ok, _ = self.cap.read()
                if not ok:
                    raise RuntimeError("No valid frames received from stream")

                logger.debug("RTSP stream opened successfully")
                return self

            except Exception as e:
                logger.error(f"Stream open failed (attempt {attempt+1}/{max_attempts}): {e}")
                if self.cap:
                    self.cap.release()
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)

        raise RuntimeError(f"Failed to open stream after {max_attempts} attempts")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def read(self):
        """Reads the latest frame from the stream."""
        # Grab the latest frame to reduce latency
        for _ in range(5):
             self.cap.grab()

        ok, frame = self.cap.retrieve()
        if not ok:
            logger.warning("Failed to read frame from RTSP stream")
            return None
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
            logger.debug("RTSP stream released")
