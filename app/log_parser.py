import re
from typing import Optional, Tuple, Dict
import datetime

LEVELS = ("TRACE", "DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL", "CRITICAL")

# Simple “good enough” parser: timestamp + level + optional logger + message
# Examples it can parse:
# 2026-01-29 10:22:01,123 INFO my.module Something happened
# 2026-01-29T10:22:01Z ERROR [Auth] Login failed
LOG_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d{3})?(?:Z)?)\s+"
    r"(?P<level>[A-Z]+)\s+"
    r"(?:(?P<logger>[\w\.\-\[\]\/]+)\s+)?"
    r"(?P<msg>.*)$"
)

def parse_line(line: str) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    raw = line.rstrip("\n")
    m = LOG_RE.match(raw)
    if not m:
        return None, None, None, raw

    ts = m.group("ts")
    level = m.group("level")
    logger = m.group("logger")
    msg = m.group("msg") or ""

    # Normalize level
    if level == "WARNING":
        level = "WARN"
    if level not in LEVELS:
        # If we matched but it's a nonstandard level, keep it anyway
        pass

    return ts, level, logger, msg

def parse_ts(ts: str) -> Optional[float]:
    if not ts:
        return None
    ts = ts.replace(',', '.')
    formats = ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%SZ"]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(ts, fmt)
            return dt.timestamp()
        except ValueError:
            pass
    return None

def fingerprint(ts: Optional[str], level: Optional[str], logger: Optional[str], msg: str) -> str:
    """
    Turn a log message into a “pattern key”.
    Keep it simple: strip numbers/uuids/hex-ish and collapse whitespace.
    This is intentionally naive but works well as a baseline.
    """
    s = msg

    # Replace UUIDs
    s = re.sub(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b", "<UUID>", s)
    # Replace long hex tokens
    s = re.sub(r"\b0x[0-9a-fA-F]+\b", "<HEX>", s)
    # Replace numbers (IDs, counts, timings)
    s = re.sub(r"\b\d+\b", "<NUM>", s)
    # Collapse spaces
    s = re.sub(r"\s+", " ", s).strip()

    # Include level + logger in key when present (useful for grouping)
    parts = []
    if level:
        parts.append(level)
    if logger:
        parts.append(logger)
    parts.append(s if s else "<EMPTY>")
    return " | ".join(parts)
