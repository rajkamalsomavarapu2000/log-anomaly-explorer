from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from collections import defaultdict
from typing import List, Dict

from .models import ParseResponse, ParsedLogLine, AnomalyResponse
from .log_parser import parse_line, fingerprint
from .anomaly import rare_pattern_anomalies

app = FastAPI(title="Log Anomaly Explorer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ok for local demo; tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return FileResponse("web/index.html")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/parse", response_model=ParseResponse)
async def api_parse(file: UploadFile = File(...)):
    data = await file.read()
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()

    sample: List[ParsedLogLine] = []
    level_counts: Dict[str, int] = defaultdict(int)
    parsed = 0

    for i, line in enumerate(lines, start=1):
        ts, level, logger, msg = parse_line(line)
        if level:
            parsed += 1
            level_counts[level] += 1

        if len(sample) < 50:
            sample.append(ParsedLogLine(
                ts=ts,
                level=level,
                logger=logger,
                message=msg if msg else (line.strip() or ""),
                raw=line,
                line_no=i
            ))

    return ParseResponse(
        total_lines=len(lines),
        parsed=parsed,
        sample=sample,
        level_counts=dict(level_counts)
    )

@app.post("/api/analyze", response_model=AnomalyResponse)
async def api_analyze(file: UploadFile = File(...), top_k: int = 10):
    data = await file.read()
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()

    keys: List[str] = []
    example_by_key: Dict[str, str] = {}

    for line in lines:
        ts, level, logger, msg = parse_line(line)
        key = fingerprint(ts, level, logger, msg if msg else line)
        keys.append(key)
        if key not in example_by_key:
            example_by_key[key] = msg if msg else line.strip()

    rare = rare_pattern_anomalies(keys, example_by_key, top_k=top_k)

    return AnomalyResponse(
        total_lines=len(lines),
        unique_patterns=len(set(keys)),
        rare_patterns=rare
    )
