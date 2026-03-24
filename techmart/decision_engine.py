"""TechMart – Silnik drzewa decyzyjnego v10

Zmiany vs v9:
    - Usunięty _sample_discount (przeniesiony do pricing.py)
    - Dodany self.product_prices (lookup UnitPrice/CostPrice)
    - Dodany self.customer_order_count (śledzenie lojalności B2B)
    - generate_row zwraca UnitSalePrice i nowy DiscountPct
    - generate_row przyjmuje active_events i pricing_rules
"""

import numpy as np
import pandas as pd

from techmart.pricing import calculate_pricing


def weighted_choice(prob_dict):
    """Losuje klucz z dict {wartość: procent}."""
    keys    = list(prob_dict.keys())
    weights = np.array([prob_dict[k] for k in keys], dtype=float)
    weights /= weights.sum()
    return keys[np.random.choice(len(keys), p=weights)]


def _build_b2c_qty_probs(qty_cfg):
    values  = np.arange(1, qty_cfg["max"] + 1)
    weights = 1.0 / (values ** qty_cfg["power"])
    return values, weights / weights.sum()


class DecisionEngine:
    """
    Generuje transakcję przejściem przez drzewo decyzyjne.
    Integruje pricing (rabaty + UnitSalePrice).
    """

    def __init__(self, tree, products, customers, lifecycle=None, pricing_rules=None):
        self.tree           = tree
        self.lifecycle       = lifecycle or {}
        self.pricing_rules   = pricing_rules or {}

        # lookup: ProductKey → Category
        self.product_category = dict(zip(products["ProductKey"], products["Category"]))

        # lookup: ProductKey → (UnitPrice, CostPrice)
        self.product_prices = {}
        for _, row in products.iterrows():
            self.product_prices[row["ProductKey"]] = (
                float(row["UnitPrice_PLN"]),
                float(row["CostPrice_PLN"]),
            )

        # produkty per kategoria
        self.products_by_cat = {}
        for _, row in products.iterrows():
            cat = row["Category"]
            self.products_by_cat.setdefault(cat, []).append(row["ProductKey"])

        # klienci per (segment, country, region)
        self.customer_index = {}
        self.customer_info  = {}
        for _, row in customers.iterrows():
            ckey    = str(row["CustomerKey"])
            seg     = row["Segment"]
            country = row["Country"]
            region  = row.get("Region")
            if pd.isna(region):
                region = None

            self.customer_info[ckey] = {
                "Segment": seg, "Country": country, "Region": region
            }
            for key in [(seg, country, region), (seg, country, None), (seg, None, None)]:
                self.customer_index.setdefault(key, []).append(ckey)

        # B2C qty
        self.b2c_qty_vals, self.b2c_qty_probs = _build_b2c_qty_probs(tree["quantity"]["B2C"])
        self.b2b_qty_cfg = tree["quantity"]["B2B"]

        # licznik zamówień per klient (do rabatu lojalnościowego B2B)
        self.customer_order_count = {}

    def generate_row(self, order_id, d_str, is_promo, batch_tracker, year,
                      month=None, active_events=None):
        """Generuje jeden wiersz transakcji."""
        t   = self.tree
        day = pd.Timestamp(d_str)

        segment      = weighted_choice(t["segment"])
        country      = weighted_choice(t["country"][segment])
        region       = weighted_choice(t["region"][country]) if country == "Polska" and country in t["region"] else None
        customer_key = self._find_customer(segment, country, region)
        channel      = weighted_choice(t["channel"][f"{segment}|{country}"])
        category     = weighted_choice(t["category"][f"{segment}|{channel}"])
        product_key  = self._sample_product_with_lifecycle(category, day)
        quantity     = self._sample_qty(segment)
        payment      = self._sample_payment(segment, country, channel, category, t)
        status       = self._sample_status(segment, channel, category, t, month)
        fulfillment  = self._sample_fulfillment(country, channel, status, t)

        # --- pricing ---
        unit_price = self.product_prices.get(product_key, (0, 0))[0]

        discount_pct, unit_sale_price = calculate_pricing(
            unit_price=unit_price,
            product_key=product_key,
            category=category,
            quantity=quantity,
            customer_key=customer_key,
            segment=segment,
            day=day,
            is_promo=is_promo,
            lifecycle=self.lifecycle,
            active_events=active_events or [],
            customer_order_count=self.customer_order_count,
            rules=self.pricing_rules,
        )

        # aktualizuj licznik zamówień klienta
        self.customer_order_count[customer_key] = self.customer_order_count.get(customer_key, 0) + 1

        return {
            "OrderID":         order_id,
            "OrderDate":       d_str,
            "CustomerKey":     customer_key,
            "ProductKey":      product_key,
            "Quantity":        quantity,
            "Channel":         channel,
            "PaymentMethod":   payment,
            "DiscountPct":     discount_pct,
            "UnitSalePrice":   unit_sale_price,
            "OrderStatus":     status,
            "FulfillmentDays": fulfillment,
            "BatchNumber":     batch_tracker.get(product_key, year),
            # ukryte — do matchowania eventów
            "_Segment":        segment,
            "_Country":        country,
            "_Region":         region,
            "_Category":       category,
        }

    # --- lifecycle ---

    def _get_lifecycle_boost(self, product_key, day):
        lc = self.lifecycle.get(product_key)
        if lc is None:
            return 1.0
        for phase in lc["phases"]:
            if phase["_date_from"] <= day <= phase["_date_to"]:
                noise = phase.get("noise", 0.0)
                if "boost_start" in phase and "boost_end" in phase:
                    total_days = (phase["_date_to"] - phase["_date_from"]).days
                    elapsed    = (day - phase["_date_from"]).days
                    progress   = elapsed / max(1, total_days)
                    base_boost = phase["boost_start"] + progress * (phase["boost_end"] - phase["boost_start"])
                else:
                    base_boost = phase.get("boost", 1.0)
                jitter = np.random.uniform(-noise, noise)
                return max(0.0, base_boost * (1 + jitter))
        return 1.0

    def _sample_product_with_lifecycle(self, category, day):
        products_in_cat = self.products_by_cat.get(category, [])
        if not products_in_cat:
            return 0
        weights = np.array([self._get_lifecycle_boost(pk, day) for pk in products_in_cat], dtype=float)
        if weights.sum() <= 0:
            return 0
        weights /= weights.sum()
        return int(np.random.choice(products_in_cat, p=weights))

    # --- pozostałe samplery ---

    def _sample_qty(self, segment):
        if segment == "B2C":
            return int(np.random.choice(self.b2c_qty_vals, p=self.b2c_qty_probs))
        cfg = self.b2b_qty_cfg
        qty = int(round(np.random.normal(cfg["mu"], cfg["sigma"])))
        return max(cfg["min"], min(cfg["max"], qty))

    def _find_customer(self, segment, country, region):
        for key in [(segment, country, region), (segment, country, None), (segment, None, None)]:
            pool = self.customer_index.get(key)
            if pool:
                return np.random.choice(pool)
        return "0"

    def _sample_payment(self, segment, country, channel, category, t):
        pm = t["payment_method"]
        for key in [f"{segment}|{country}|{channel}", f"{segment}|{country}", f"{segment}|_default"]:
            if key in pm:
                base = dict(pm[key])
                break
        else:
            return "Przelew"
        mods = pm.get("_modifiers", {})
        if category in mods.get("raty_boost_categories", []) and "Raty" in base:
            boost_pp    = mods.get("raty_boost_pp", 0)
            reduce_from = mods.get("raty_reduce_from", [])
            base["Raty"] += boost_pp
            per_source    = boost_pp / max(1, len(reduce_from))
            for src in reduce_from:
                if src in base:
                    base[src] = max(0.5, base[src] - per_source)
        return weighted_choice(base)

    def _sample_status(self, segment, channel, category, t, month=None):
        st   = t["order_status"]
        base = dict(st[segment])
        mods = st.get("_modifiers", {})
        for trigger, pp in mods.get("return_boost", {}).items():
            if trigger in (category, channel):
                base["Zwrócone"]     = base.get("Zwrócone", 0) + pp
                base["Zrealizowane"] = base.get("Zrealizowane", 100) - pp
        for trigger, pp in mods.get("return_reduce", {}).items():
            if trigger in (category, channel):
                base["Zwrócone"]     = max(0.5, base.get("Zwrócone", 0) - pp)
                base["Zrealizowane"] = base.get("Zrealizowane", 100) + pp
        seasonal = mods.get("seasonal_return_mult", {})
        if month is not None and str(month) in seasonal:
            mult = seasonal[str(month)]
            boost_pp = base.get("Zwrócone", 0) * (mult - 1.0)
            base["Zwrócone"]     = base.get("Zwrócone", 0) + boost_pp
            base["Zrealizowane"] = base.get("Zrealizowane", 100) - boost_pp
        return weighted_choice(base)

    def _sample_fulfillment(self, country, channel, status, t):
        ff = t["fulfillment_days"]
        for key in [status, channel, f"{country}|{channel}"]:
            if key in ff:
                cfg = ff[key]
                break
        else:
            return 3
        if "days" in cfg:
            return cfg["days"]
        roll  = np.random.uniform(0, 100)
        cumul = 0.0
        for tier in cfg["tiers"]:
            cumul += tier["pct"]
            if roll <= cumul:
                lo, hi = tier["range"]
                return int(np.random.randint(lo, hi + 1))
        lo, hi = cfg["tiers"][-1]["range"]
        return int(np.random.randint(lo, hi + 1))
