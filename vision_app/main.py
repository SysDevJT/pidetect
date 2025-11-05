import time
import logging
from datetime import datetime, timezone
from .config import Config, apply_ffmpeg_settings, apply_ultralytics_settings, apply_picam_settings
from .utils.logging_setup import setup_logging
from .streams.rtsp import RTSPStream
from .streams.picam import PiCamStream, is_picam_available
from .detection.yolo_detector import YoloDetector
from .analysis.tracker import SeenTracker
from .analysis.lmstudio_analyzer import analyze_with_lmstudio
from .analysis.parsers import extract_vision_objects, extract_vision_actions
from .outputs.tui import Dashboard
from .outputs.webhook import send_to_webhook
import cv2
import numpy as np
import base64

logger = logging.getLogger(__name__)

_prev_small = None

def motion_changed(frame_bgr):
    global _prev_small
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (Config.FRAME_SIZE[0] // 8, Config.FRAME_SIZE[1] // 8))

    if _prev_small is None:
        _prev_small = small
        return True

    diff = cv2.absdiff(small, _prev_small)
    score = float(np.mean(diff))
    _prev_small = small
    return score >= Config.MOTION_THRESH

def save_snapshot(frame_bgr):
    ok, enc = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), Config.JPEG_QUALITY])
    if not ok:
        raise RuntimeError("Failed to encode snapshot")

    data = enc.tobytes()
    b64 = base64.b64encode(data).decode("ascii")
    return b64

def process_frame(frame, detector, trackers):
    if frame is None:
        return None

    if not motion_changed(frame):
        return None

    tracker_yolo, tracker_vision, tracker_actions = trackers
    result = detector.detect(frame)

    if not result["objects"]:
        return None

    # YOLO labels bijhouden
    tracker_yolo.update([o["label"] for o in result["objects"]])

    # Snapshot
    try:
        snap_b64 = save_snapshot(frame)
    except Exception as e:
        logger.error(f"Snapshot error: {e}")
        snap_b64 = None

    vision = {}
    if snap_b64:
        vision = analyze_with_lmstudio(snap_b64) or {}
        if vision.get("status") == "ok":
            parsed = vision.get("parsed") or {}

            if parsed:
                objs = parsed.get("objects_present") or []
                acts = parsed.get("actions_present") or []

                if objs:
                    tracker_vision.update(objs)
                if acts:
                    tracker_actions.update(acts)

                # compacte tag-samenvatting
                vision["tags_summary"] = f"objects={len(objs)} | actions={len(acts)}"

                # mooie tekst-samenvatting: eerst summary_text, anders bestaande summary
                st = parsed.get("summary_text") or vision.get("summary")
                if st:
                    vision["summary"] = st
            else:
                # JSON-pad niet gebruikt → fallback: prose analyseren
                vsum = vision.get("summary") or ""
                vis_objs = extract_vision_objects(vsum)
                if vis_objs:
                    tracker_vision.update(vis_objs)
                vis_actions = extract_vision_actions(vsum)
                if vis_actions:
                    tracker_actions.update(vis_actions)

    out = {
        "source": Config.DETECTORNAME,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "summary": result["summary"],   # YOLO-samenvatting
        "objects": result["objects"],
        "vision": vision,
    }
    send_to_webhook(out)
    return out


def obsolete_process_frame(frame, detector, trackers):
    if frame is None:
        return None

    if not motion_changed(frame):
        return None

    tracker_yolo, tracker_vision, tracker_actions = trackers
    result = detector.detect(frame)

    if result["objects"]:
        tracker_yolo.update([o["label"] for o in result["objects"]])

        try:
            snap_b64 = save_snapshot(frame)
        except Exception as e:
            logger.error(f"Snapshot error: {e}")
            snap_b64 = None

        vision = {}
        if snap_b64:
            vision = analyze_with_lmstudio(snap_b64)
            if vision.get("status") == "ok":
                if "parsed" in vision and vision["parsed"]:
                    objs = vision["parsed"].get("objects_present", [])
                    acts = vision["parsed"].get("actions_present", [])
                    if objs: tracker_vision.update(objs)
                    if acts: tracker_actions.update(acts)
                    vision["tags_summary"] = f"objects={len(objs)} | actions={len(acts)}"
                    st = parsed.get("summary_text")
                    if st:
                      vision["summary"] = st
                else:
                    vsum = vision.get("summary", "")
                    vis_objs = extract_vision_objects(vsum)
                    if vis_objs: tracker_vision.update(vis_objs)
                    vis_actions = extract_vision_actions(vsum)
                    if vis_actions: tracker_actions.update(vis_actions)

        out = {
            "source": Config.DETECTORNAME,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "summary": result["summary"],
            "objects": result["objects"],
            "vision": vision
        }
        send_to_webhook(out)
        return out

    return None

def main_loop():
    apply_ffmpeg_settings()
    apply_ultralytics_settings()
    apply_picam_settings()
    setup_logging()

    dashboard = Dashboard()
    dashboard.start()

    detector = YoloDetector(Config.MODEL_PATH)
    tracker_yolo = SeenTracker(ttl=1800)
    tracker_vision = SeenTracker(ttl=3600)
    tracker_actions = SeenTracker(ttl=1800)

    dashboard.set_seen_sources(
        yolo_fn=tracker_yolo.snapshot,
        vision_fn=tracker_vision.snapshot,
        actions_fn=tracker_actions.snapshot,
    )

    last_call_t = 0.0
    interval = 1.0 / max(1, Config.FPS_SAMPLING)

    try:
        while True:
            use_picam = Config.USE_PICAM and is_picam_available()
            source_label = "picam" if use_picam else "rtsp"
            dashboard.set_cam_status(f"opening ({source_label})")

            try:
                stream_provider = PiCamStream() if use_picam else RTSPStream(Config.RTSP_URL)

                with stream_provider as stream:
                    open_timestamp = time.time()
                    dashboard.set_cam_status(f"open ({source_label})")

                    while True:
                        if dashboard.enabled:
                            ch = dashboard.scr.getch()
                            if ch in (ord('q'), ord('Q')):
                                return
                            if ch in (ord('r'), ord('R')):
                                tracker_yolo.clear()
                                tracker_vision.clear()
                                tracker_actions.clear()
                                dashboard.set_error("Memory reset")

                        if time.time() - open_timestamp > Config.REOPEN_EVERY_S:
                            logger.debug("Reopening stream for stability")
                            break

                        now = time.time()
                        if now - last_call_t < interval:
                            time.sleep(0.01)
                            continue

                        last_call_t = now
                        frame = stream.read()

                        if frame is not None:
                            result = process_frame(frame, detector, (tracker_yolo, tracker_vision, tracker_actions))
                            if result:
                                dashboard.update(result)

            except Exception as e:
                msg = f"Stream error: {e}"
                logger.error(msg)
                dashboard.set_error(msg)
                time.sleep(5)

    finally:
        dashboard.stop()
