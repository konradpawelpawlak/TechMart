"""TechMart – Ładowanie plików konfiguracyjnych i wymiarów"""

import json
import os
import pandas as pd

from techmart.config import (
    DIM_PRODUCT_FILE, DIM_CUSTOMER_FILE,
    DECISION_TREE_FILE, CUSTOM_EVENTS_FILE,
    PRODUCT_LIFECYCLE_FILE, PRICING_RULES_FILE,
)


def script_path(filename):
    """Ścieżka relatywna do katalogu głównego skryptu (rodzic techmart/)."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename)


def load_dimensions():
    for f in [DIM_PRODUCT_FILE, DIM_CUSTOMER_FILE]:
        if not os.path.exists(script_path(f)):
            raise FileNotFoundError(f"Nie znaleziono: {script_path(f)}")
    return pd.read_csv(script_path(DIM_PRODUCT_FILE)), pd.read_csv(script_path(DIM_CUSTOMER_FILE))


def load_decision_tree():
    path = script_path(DECISION_TREE_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Nie znaleziono: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_custom_events():
    path = script_path(CUSTOM_EVENTS_FILE)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        events = json.load(f)
    for ev in events:
        ev["_date_from"] = pd.Timestamp(ev["date_from"])
        ev["_date_to"]   = pd.Timestamp(ev["date_to"])
        ev.setdefault("filters", {})
        ev.setdefault("noise", 0.0)
    return events


def load_product_lifecycle():
    path = script_path(PRODUCT_LIFECYCLE_FILE)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    lifecycle = {}
    for pk_str, cfg in raw.items():
        pk = int(pk_str)
        phases = []
        for phase in cfg["phases"]:
            p = dict(phase)
            p["_date_from"] = pd.Timestamp(phase.get("date_from", "1900-01-01"))
            p["_date_to"]   = pd.Timestamp(phase.get("date_to", "2099-12-31"))
            phases.append(p)
        lifecycle[pk] = {"name": cfg["name"], "phases": phases}
    return lifecycle


def load_pricing_rules():
    path = script_path(PRICING_RULES_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Nie znaleziono: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
