from time import time

class SeenTracker:
    """
    Tracks detected objects, including their count, last seen time, and current presence.
    """
    def __init__(self, ttl=None):
        self.ttl = ttl
        self.data = {}  # label -> {count, last_seen, present}

    def update(self, labels_now):
        """
        Updates the tracker with the latest set of detected labels.
        """
        now = time()
        for v in self.data.values():
            v["present"] = False

        for lab in labels_now:
            rec = self.data.setdefault(lab, {"count": 0, "last_seen": 0.0, "present": False})
            rec["count"] += 1
            rec["last_seen"] = now
            rec["present"] = True

        if self.ttl is not None:
            cutoff = now - self.ttl
            self.data = {k: v for k, v in self.data.items() if v["last_seen"] >= cutoff}

    def clear(self):
        """
        Resets the tracker's memory.
        """
        self.data.clear()

    def snapshot(self):
        """
        Returns a copy of the current tracking data.
        """
        return {k: dict(v) for k, v in self.data.items()}
