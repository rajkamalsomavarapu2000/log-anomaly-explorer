from typing import List, Dict, Tuple
from collections import Counter

from .models import AnomalyItem

def rare_pattern_anomalies(pattern_keys: List[str], original_messages: Dict[str, str], top_k: int = 10) -> List[AnomalyItem]:
    """
    Baseline anomaly detector:
    - Compute pattern frequencies
    - Return patterns with the lowest counts (but > 0)
    """
    c = Counter(pattern_keys)
    if not c:
        return []

    # sort by count asc, then key
    items = sorted(c.items(), key=lambda x: (x[1], x[0]))
    rare = items[:top_k]

    out: List[AnomalyItem] = []
    for key, count in rare:
        out.append(AnomalyItem(
            key=key,
            count=count,
            example_message=original_messages.get(key, "")
        ))
    return out
