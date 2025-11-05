import curses
import textwrap
from datetime import datetime
from time import time

class Dashboard:
    """
    A terminal-based user interface for displaying detection events and system status.
    """
    def __init__(self):
        self.scr = None
        self.enabled = False
        self.last_event = None
        self.last_err = None
        self.cam_status = "initializing"
        self.event_count = 0
        self.get_seen_yolo = None
        self.get_seen_vision = None
        self.get_seen_actions = None

    def start(self):
        try:
            self.scr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            self.scr.nodelay(True)
            self.enabled = True
        except Exception as e:
            self.enabled = False
            print(f"TUI disabled: {e}")

    def stop(self):
        if self.enabled:
            curses.nocbreak()
            curses.echo()
            curses.endwin()
            self.enabled = False

    def set_seen_sources(self, yolo_fn=None, vision_fn=None, actions_fn=None):
        self.get_seen_yolo = yolo_fn
        self.get_seen_vision = vision_fn
        self.get_seen_actions = actions_fn

    def set_cam_status(self, status: str):
        self.cam_status = status
        self.draw()

    def set_error(self, err: str):
        self.last_err = err
        self.draw()

    def update(self, event: dict):
        self.last_event = event
        self.event_count += 1
        self.draw()

    def _render_memory(self, title, seen_fn, addln):
        if not callable(seen_fn):
            return

        seen = seen_fn()
        if not seen:
            return

        addln(f" {title}:", curses.A_BOLD)
        items = sorted(seen.items(), key=lambda kv: (not kv[1]["present"], kv[0]))
        now_ts = time()

        for label, meta in items[:40]:
            mark = "✔" if meta.get("present") else "□"
            ago = int(now_ts - meta.get("last_seen", now_ts))
            ago_str = f"{ago}s" if ago < 60 else f"{ago//60}m{ago%60:02d}s"
            line_txt = f"  {mark} {label:<22}  count={meta.get('count',0):<3}  last={ago_str} ago"
            addln(line_txt)
        addln()

    def draw(self):
        if not self.enabled:
            return
        try:
            self.scr.erase()
            h, w = self.scr.getmaxyx()
            line = 0

            def addln(s="", style=curses.A_NORMAL):
                nonlocal line
                if line < h:
                    try:
                        self.scr.addnstr(line, 0, s, w-1, style)
                    except curses.error:
                        pass
                    line += 1

            addln(" RTSP/PiCam Vision Monitor  —  press q to exit ", curses.A_REVERSE)
            addln(f" Camera: {self.cam_status}   |   Events: {self.event_count}   |   Time: {datetime.now().strftime('%H:%M:%S')}")
            addln()

            if self.last_event:
                addln(" Last detection:", curses.A_BOLD)
                addln(f"  Time:       {self.last_event.get('timestamp')}")
                addln(f"  Summary:    {self.last_event.get('summary')}")

                objs = self.last_event.get("objects") or []
                obj_str = ", ".join(f"{o['label']}({o['confidence']:.2f})" for o in objs) if objs else "-"
                addln(f"  Objects:    {obj_str}")

                vision = self.last_event.get("vision") or {}
                vstat = vision.get("status", "-")
                addln(f"  Vision:     {vstat}")

                vsum = vision.get("summary")
                if not vsum and vstat != "ok":
                    verr = vision.get("error") or ""
                    vbody = vision.get("body") or ""
                    vsum = f"(error) {verr or vbody or '-'}"

                if vsum:
                    addln("  Vision summary:")
                    lines = [ln for para in str(vsum).splitlines() for ln in textwrap.wrap(para, width=max(20, w-4))]
                    for ln in lines[:14]:
                        addln("    " + ln)
                    if len(lines) > 14:
                        addln("    ... (truncated)")
                addln()

            self._render_memory("Observed objects (YOLO)", self.get_seen_yolo, addln)
            self._render_memory("Vision objects (LM Studio)", self.get_seen_vision, addln)
            self._render_memory("Vision actions (LM Studio)", self.get_seen_actions, addln)

            if self.last_err:
                addln(" Last error:", curses.A_BOLD)
                for ln in textwrap.wrap(self.last_err, width=max(20, w-4)):
                    addln("  " + ln)

            addln()
            addln(("-"* (w-1))[:w-1])
            addln(" q = quit | r = reset memory | Logs still written to file if configured")

            self.scr.refresh()
        except Exception as e:
            self.stop()
            print(f"TUI error: {e}")
