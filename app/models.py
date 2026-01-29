from pydantic import BaseModel
from typing import List, Optional, Dict

class ParsedLogLine(BaseModel):
    ts: Optional[str] = None
    level: Optional[str] = None
    logger: Optional[str] = None
    message: str
    raw: str
    line_no: int

class ParseResponse(BaseModel):
    total_lines: int
    parsed: int
    sample: List[ParsedLogLine]
    level_counts: Dict[str, int]

class AnomalyItem(BaseModel):
    key: str
    count: int
    example_message: str

class AnomalyResponse(BaseModel):
    total_lines: int
    unique_patterns: int
    rare_patterns: List[AnomalyItem]
