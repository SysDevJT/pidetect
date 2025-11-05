import os

class Config:
    RTSP_URL = os.getenv("RTSP_URL")
    MODEL_PATH = os.getenv("YOLO_MODEL", "yolov8n.pt")
    FPS_SAMPLING = int(os.getenv("FPS_SAMPLING", "1"))
    FRAME_SIZE = tuple(map(int, os.getenv("FRAME_SIZE", "640,480").split(",")))  # (w,h)
    CONF_MIN = float(os.getenv("CONF_MIN", "0.5"))
    WEBHOOK = os.getenv("N8N_URL")
    MOTION_THRESH = float(os.getenv("MOTION_THRESH", "5.0"))
    REOPEN_EVERY_S = int(os.getenv("REOPEN_EVERY_S", "60"))
    MAX_RECONNECT_ATTEMPTS = int(os.getenv("MAX_RECONNECT_ATTEMPTS", "3"))
    FFMPEG_TIMEOUT = int(os.getenv("FFMPEG_TIMEOUT", "5000000"))  # microseconds
    DETECTORNAME= os.getenv("DETECTORNAME", "UnnamedDetector")
    # Primair bron kiezen: picam of rtsp
    USE_PICAM = os.getenv("USE_PICAM", "1").lower() in ("1", "true", "yes")

    # LM Studio (OpenAI-compatible)
    LMSTUDIO_URL = os.getenv("LMSTUDIO_URL", "http://127.0.0.1:1234").rstrip("/")
    LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "qwen/qwen2.5-vl-7b")

    # Snapshots
    JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "92"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def apply_ffmpeg_settings():
    """Apply FFmpeg/RTSP stability settings."""
    os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
    os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "quiet"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
        f"rtsp_transport;tcp|fflags;discardcorrupt|flags;low_delay|"
        f"reorder_queue_size;0|buffer_size;2048000|probesize;500000|"
        f"analyzeduration;1000000|rw_timeout;{Config.FFMPEG_TIMEOUT}|"
        f"stimeout;{Config.FFMPEG_TIMEOUT}|max_delay;500000|err_detect;ignore_err"
    )

def apply_ultralytics_settings():
    """Silence Ultralytics/YOLO outputs."""
    os.environ["ULTRALYTICS_AGC"] = "0"
    os.environ["ULTRALYTICS_HUB"] = "0"
    os.environ["ULTRALYTICS_VERBOSE"] = "False"

def apply_picam_settings():
    """Silence Libcamera outputs."""
    os.environ.setdefault("LIBCAMERA_LOG_LEVELS", "4") # 4 = FATAL
