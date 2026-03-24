"""TechMart – Obliczanie rabatów i ceny sprzedaży (UnitSalePrice)

Warstwy rabatów (kumulują się, cap z pricing_rules):
    1. Aging       — miesiące od premiery produktu (z lifecycle)
    2. Quantity    — progi ilościowe
    3. Loyalty     — liczba historycznych zamówień klienta (tylko B2B)
    4. Seasonal    — promocje sezonowe (PROMOTION_DATES + custom events)
"""

import pandas as pd


def _months_since_premiere(product_key, day, lifecycle):
    """Oblicza ile miesięcy minęło od premiery produktu."""
    lc = lifecycle.get(product_key)
    if lc is None:
        return 0

    for phase in lc["phases"]:
        boost = phase.get("boost", phase.get("boost_start", 0))
        if boost > 0:
            premiere = phase["_date_from"]
            delta = (day - premiere).days
            return max(0, delta // 30)

    return 0


def _tier_lookup(tiers, value, value_key):
    """Szuka progu w liście tierów."""
    for tier in tiers:
        if value <= tier[value_key]:
            return tier["discount"]
    return tiers[-1]["discount"]


def _aging_discount(product_key, day, lifecycle, rules):
    """Warstwa 1: rabat za wiek produktu."""
    months = _months_since_premiere(product_key, day, lifecycle)
    return _tier_lookup(rules["aging_tiers"], months, "months_max")


def _quantity_discount(quantity, rules):
    """Warstwa 2: rabat za wielkość zamówienia."""
    return _tier_lookup(rules["quantity_tiers"], quantity, "qty_max")


def _loyalty_discount(customer_key, segment, customer_order_count, rules):
    """Warstwa 3: rabat lojalnościowy (tylko B2B)."""
    if segment != "B2B":
        return 0
    orders = customer_order_count.get(customer_key, 0)
    return _tier_lookup(rules["loyalty_tiers"], orders, "orders_max")


def _seasonal_discount(is_promo, product_key, category, day, lifecycle,
                        active_events, rules):
    """Warstwa 4: rabat promocyjny (w okresie promocji)."""
    if not is_promo:
        return 0

    seasonal = rules["seasonal_discounts"]

    months = _months_since_premiere(product_key, day, lifecycle)
    if months >= rules.get("clearance_aging_months", 24):
        return seasonal["clearance"]

    for ev in active_events:
        if ev["boost"] >= 1.0:
            cat_filter = ev["filters"].get("Category", [])
            if category in cat_filter:
                return seasonal["category_event"]

    return seasonal["standard"]


def calculate_pricing(unit_price, product_key, category, quantity,
                       customer_key, segment, day, is_promo,
                       lifecycle, active_events, customer_order_count,
                       rules):
    """
    Oblicza DiscountPct i UnitSalePrice.
    Zwraca tuple (discount_pct, unit_sale_price).
    """
    d1 = _aging_discount(product_key, day, lifecycle, rules)
    d2 = _quantity_discount(quantity, rules)
    d3 = _loyalty_discount(customer_key, segment, customer_order_count, rules)
    d4 = _seasonal_discount(is_promo, product_key, category, day,
                             lifecycle, active_events, rules)

    cap = rules.get("discount_cap", 40)
    discount_pct = min(cap, d1 + d2 + d3 + d4)

    unit_sale_price = round(unit_price * (1 - discount_pct / 100), 2)

    return discount_pct, unit_sale_price
