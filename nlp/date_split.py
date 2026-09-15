"""Conservative post-cluster split of a fused cluster into per-event sub-clusters
by resolved Athens event-day. Fail-safe: worst case it returns the cluster
unchanged. Never over-splits a clean single-date cluster."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import numpy as np


def _bucket_days(dated: list[tuple[str, date]], tolerance_days: int) -> dict[date, list[str]]:
    by_day: dict[date, list[str]] = defaultdict(list)
    for aid, d in dated:
        by_day[d].append(aid)
    buckets: dict[date, list[str]] = {}
    rep: date | None = None
    prev: date | None = None
    for d in sorted(by_day):
        if prev is not None and (d - prev).days <= tolerance_days:
            buckets[rep].extend(by_day[d])
        else:
            rep = d
            buckets[rep] = list(by_day[d])
        prev = d
    return buckets


def split_by_event_day(
    articles: list[tuple[str, np.ndarray, date | None]],
    min_bucket: int,
    tolerance_days: int,
) -> list[list[str]]:
    all_ids = [aid for aid, _v, _d in articles]
    dated = [(aid, d) for aid, _v, d in articles if d is not None]
    undated = [aid for aid, _v, d in articles if d is None]
    if not dated:
        return [all_ids]

    buckets = _bucket_days(dated, tolerance_days)
    eligible = {k: v for k, v in buckets.items() if len(v) >= min_bucket}
    if len(eligible) <= 1:
        return [all_ids]  # nothing to peel → unchanged (fail-safe)

    # Largest eligible bucket is the primary; ties broken toward the earliest day.
    primary_key = max(eligible, key=lambda k: (len(eligible[k]), -k.toordinal()))
    below_threshold = [aid for k, v in buckets.items() if k not in eligible for aid in v]

    groups: list[list[str]] = []
    for k, ids in eligible.items():
        if k == primary_key:
            groups.append(ids + below_threshold + undated)
        else:
            groups.append(list(ids))
    return groups
