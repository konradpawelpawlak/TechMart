"""TechMart – Ładowanie plików konfiguracyjnych i wymiarów"""

import json
import os
import sys

import pandas as pd

from techmart.config import (
    DIM_PRODUCT_FILE, DIM_CUSTOMER_FILE,
    DECISION_TREE_FILE, CUSTOM_EVENTS_FILE,
    PRODUCT_LIFECYCLE_FILE, PRICING_RULES_FILE,
)


def _frozen():
    return getattr(sys, "frozen", False) is True


def resource_path(filename):
    """Pliki do odczytu: przy .exe w pakiecie PyInstaller (MEIPASS), inaczej katalog projektu."""
    if _frozen():
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


def output_path(filename):
    """Zapis wyników CSV: obok pliku .exe po zbudowaniu; lokalnie – katalog projektu."""
    if _frozen():
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


def script_path(filename):
    """Alias dla kompatybilności – wejścia z pakietu / projektu."""
    return resource_path(filename)


def load_dimensions():
    prod_p = resource_path(DIM_PRODUCT_FILE)
    cust_p = output_path(DIM_CUSTOMER_FILE)
    if not os.path.exists(prod_p):
        raise FileNotFoundError(f"Nie znaleziono: {prod_p}")
    if not os.path.exists(cust_p):
        raise FileNotFoundError(
            f"Nie znaleziono: {cust_p}\n"
            "Najpierw uruchom generator klientów (DimCustomer), potem sprzedaż."
        )
    return pd.read_csv(prod_p), pd.read_csv(cust_p)


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
