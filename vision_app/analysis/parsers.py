import re

NEGATIVE_PATTERNS = [r"\bno (animal|animals)\b", r"\bnone visible\b", r"\bnot visible\b", r"\bno .* present\b"]

def norm_item(s: str) -> str:
    """Lowercase, remove parentheses, non-alphanum chars, and articles."""
    if not s:
        return ""
    s = re.sub(r"\(.*?\)", "", s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9 _\-]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(a|an|the)\s+", "", s)
    return s

def head_noun_phrase(s: str) -> str:
    """Extract a short head noun phrase from a sentence."""
    s = norm_item(s)
    parts = re.split(r"\s*[:\-]\s*| is | are | with | of ", s, maxsplit=1)
    s = parts[0]
    words = s.split()
    return " ".join(words[:3])

def is_negative_phrase(s: str) -> bool:
    s = (s or "").lower()
    return any(re.search(p, s) for p in NEGATIVE_PATTERNS)

def dedupe_and_filter(items):
    out, seen = [], set()
    for it in items:
        if not it or len(it) <= 1:
            continue
        if is_negative_phrase(it):
            continue
        it = re.sub(r"\s+", " ", it).strip()
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out

HEADING_RE = re.compile(r"^\s*#{1,6}\s*(.+?):?\s*$", re.IGNORECASE)
BULLET_RE  = re.compile(r"^\s*[-*•]\s+(.*\S)\s*$")
NUM_RE     = re.compile(r"^\s*\d+[.)]\s+(.*\S)\s*$")

def _collect_section(lines, start_idx):
    items, i = [], start_idx + 1
    while i < len(lines):
        line = lines[i].rstrip()
        if HEADING_RE.match(line):
            break
        m = BULLET_RE.match(line) or NUM_RE.match(line)
        if m:
            items.append(m.group(1))
        i += 1
    return items

def extract_vision_objects(text: str):
    if not text:
        return []
    lines, raw = text.splitlines(), []
    for idx, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m and "object" in (m.group(1) or "").strip().lower():
            raw = _collect_section(lines, idx)
            break
    if not raw:
        current = "other"
        for line in lines:
            hm = HEADING_RE.match(line)
            if hm:
                t = (hm.group(1) or "").strip().lower()
                if "action" in t: current = "actions"
                elif "object" in t: current = "objects"
                else: current = "other"
                continue
            bm = BULLET_RE.match(line) or NUM_RE.match(line)
            if bm and current in ("objects", "other"):
                raw.append(bm.group(1))

    normed = [head_noun_phrase(x) for x in raw if x]
    normed = [re.sub(r"\s+", "_", z) for z in normed]
    return dedupe_and_filter(normed)

def extract_vision_actions(text: str):
    if not text:
        return []
    lines, raw = text.splitlines(), []
    for idx, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m and "action" in (m.group(1) or "").strip().lower():
            raw = _collect_section(lines, idx)
            break
    if not raw:
        lowered = text.lower()
        raw += [m.group(1).strip() for m in re.finditer(r"\bappears to be ([a-z][a-z\s\-]+?)(?:[.,;\n]|$)", lowered)]
        raw += [m.group(1).strip() for m in re.finditer(r"\bis ([a-z]+ing)(?:[^\w]|$)", lowered)]

    normed = [head_noun_phrase(x) for x in raw if x]
    normed = [re.sub(r"\s+", "_", z) for z in normed]

    DROP = {"home_office", "study_area", "daytime", "lighting", "wearing"}
    out = [c for c in dedupe_and_filter(normed) if c not in DROP]
    return out
