"""TechMart – Custom events (nakładki czasowe na dane)"""

import numpy as np

_EVENT_FIELD_MAP = {
    "Segment":  "_Segment",
    "Country":  "_Country",
    "Region":   "_Region",
    "Category": "_Category",
    "Channel":  "Channel",
}


def get_active_events(events, day):
    return [ev for ev in events if ev["_date_from"] <= day <= ev["_date_to"]]


def compute_event_multiplier(ev):
    noise  = ev.get("noise", 0.0)
    jitter = np.random.uniform(-noise, noise)
    return ev["boost"] * (1 + jitter)


def row_matches_event(row, ev):
    for col, allowed in ev["filters"].items():
        field = _EVENT_FIELD_MAP.get(col, col)
        val   = row.get(field)
        if val is None:
            return False
        if val not in allowed:
            return False
    return True


def apply_custom_events(day_sales, active_events, oid_counter,
                         engine, batch_tracker, year, d_str, is_promo,
                         month=None):
    for ev in active_events:
        multiplier = compute_event_multiplier(ev)

        matching_idx = [i for i, row in enumerate(day_sales) if row_matches_event(row, ev)]
        n_matching   = len(matching_idx)

        if n_matching == 0:
            if multiplier >= 1.0:
                n_extra = max(1, int(round((multiplier - 1.0) * 3)))
            else:
                continue
        elif multiplier >= 1.0:
            n_extra = max(0, int(round(n_matching * (multiplier - 1.0))))
        else:
            n_remove = min(n_matching, int(round(n_matching * (1.0 - multiplier))))
            if n_remove > 0:
                remove_idx = set(np.random.choice(matching_idx, size=n_remove, replace=False))
                day_sales  = [row for i, row in enumerate(day_sales) if i not in remove_idx]
            continue

        for _ in range(n_extra):
            oid_counter += 1
            row = engine.generate_row(oid_counter, d_str, is_promo, batch_tracker, year,
                                       month, active_events)
            for _attempt in range(50):
                if row_matches_event(row, ev):
                    break
                oid_counter += 1
                row = engine.generate_row(oid_counter, d_str, is_promo, batch_tracker, year,
                                           month, active_events)
            day_sales.append(row)

    return day_sales, oid_counter
