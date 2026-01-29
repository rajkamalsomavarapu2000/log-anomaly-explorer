from typing import List, Dict, Tuple
from collections import Counter, defaultdict
import statistics



from .models import AnomalyItem, SpikeItem
from .log_parser import parse_line, fingerprint, parse_ts

def rare_pattern_anomalies(
    pattern_keys: List[str],
    original_messages: Dict[str, str],
    top_k: int = 10
) -> List[AnomalyItem]:

    c = Counter(pattern_keys)
    if not c:
        return []

    total = sum(c.values())
    unique = len(c)
    avg = total / unique if unique else 0

    items = sorted(c.items(), key=lambda x: (x[1], x[0]))[:top_k]

    out: List[AnomalyItem] = []
    for key, count in items:
        score = (avg - count) / avg if avg > 0 else 0
        out.append(AnomalyItem(
            key=key,
            count=count,
            score=round(score, 2),
            explanation=f"This pattern appears {count} times, which is lower than the average frequency.",
            example_message=original_messages.get(key, ""),
            cluster_id=0
        ))
    return out

def spike_anomalies(lines: List[str], window_size: int = 60, threshold_mult: float = 2.0, top_k: int = 10) -> List[SpikeItem]:
    """
    Detect spikes in log patterns within time windows.
    """
    window_counts = defaultdict(int)
    example_by_key_window = {}
    keys = []

    for line in lines:
        ts_str, level, logger, msg = parse_line(line)
        if not ts_str:
            continue
        ts = parse_ts(ts_str)
        if ts is None:
            continue
        key = fingerprint(ts_str, level, logger, msg if msg else line)
        window = int(ts // window_size) * window_size
        window_key = (key, window)
        window_counts[window_key] += 1
        if window_key not in example_by_key_window:
            example_by_key_window[window_key] = msg if msg else line.strip()
        keys.append(key)

    unique_patterns = len(set(keys))

    spikes = []
    key_windows = defaultdict(list)
    for (key, window), count in window_counts.items():
        key_windows[key].append((window, count))

    for key, windows in key_windows.items():
        if len(windows) <= 1:
            continue
        counts = [c for w, c in windows]
        mean = statistics.mean(counts)
        stdev = statistics.stdev(counts) if len(counts) > 1 else 0
        threshold = mean + threshold_mult * stdev
        for window, count in windows:
            if count > threshold and count > 1:
                score = (count - mean) / stdev if stdev > 0 else 0
                explanation = f"This pattern spiked to {count} occurrences in the window starting at {window}, {score:.1f} standard deviations above the pattern's average."
                spikes.append(SpikeItem(
                    key=key,
                    window_ts=window,
                    count=count,
                    score=round(score, 2),
                    explanation=explanation,
                    example_message=example_by_key_window.get((key, window), "")
                ))

    spikes.sort(key=lambda x: (-x.score, x.key))
    spikes = spikes[:top_k]

    # Clustering
    clusters_dict = {}
    try:
        if len(spikes) > 1:
            texts = [item.example_message for item in spikes]
            vectorizer = TfidfVectorizer(stop_words='english')
            X = vectorizer.fit_transform(texts)
            n_clusters = min(5, len(spikes))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X)
            for i, item in enumerate(spikes):
                item.cluster_id = int(clusters[i])
            # Summaries
            feature_names = vectorizer.get_feature_names_out()
            for c in range(n_clusters):
                cluster_items = [item for item, cl in zip(spikes, clusters) if cl == c]
                count = len(cluster_items)
                examples = [item.example_message for item in cluster_items[:3]]
                # Top terms
                centroid = kmeans.cluster_centers_[c]
                top_indices = centroid.argsort()[-5:][::-1]
                top_terms = [feature_names[idx] for idx in top_indices if idx < len(feature_names)]
                clusters_dict[c] = ClusterSummary(count=count, top_terms=top_terms, examples=examples)
        else:
            for item in spikes:
                item.cluster_id = 0
            if len(spikes) == 1:
                clusters_dict[0] = ClusterSummary(count=1, top_terms=[], examples=[spikes[0].example_message])
    except Exception as e:
        print(f"Clustering error: {e}")
        for item in spikes:
            item.cluster_id = 0
        clusters_dict[0] = ClusterSummary(count=len(spikes), top_terms=[], examples=[item.example_message for item in spikes[:3]])

    return spikes
