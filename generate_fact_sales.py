"""
"""
"""
TechMart – Generator danych sprzedażowych (FactSales) v10
==========================================================
Uruchomienie:
    python generate_dim_customer.py   <- najpierw klienci
    python generate_fact_sales.py     <- potem fakty

Nowosci v10:
    - 4 warstwy rabatow: aging, quantity, loyalty (B2B), seasonal
    - UnitSalePrice w FactSales
    - pricing_rules.json - progi rabatowe
    - Wycofanie produktow (iPhone 13, Samsung S22, Huawei MatePad, HP Spectre)
"""

import numpy as np
import pandas as pd

from techmart.config import (
    VERSION, START_DATE, END_DATE, BASE_DAILY_ORDERS,
    DOW_BASE_PROFILE, DOW_NOISE_SIGMA, DAILY_LOGNORMAL_SIGMA,
    POLISH_HOLIDAYS, DECISION_TREE_FILE,
)
from techmart.loaders import (
    load_dimensions, load_decision_tree,
    load_custom_events, load_product_lifecycle,
    load_pricing_rules,
)
from techmart.daily_factors import (
    build_year_factors, build_month_factors,
    build_promo_map, build_spike_map,
)
from techmart.decision_engine import DecisionEngine
from techmart.custom_events import get_active_events, apply_custom_events
from techmart.batch_tracker import BatchTracker
from techmart.summary import print_summary
from techmart.save_outputs import save_outputs

_HIDDEN_COLS = ["_Segment", "_Country", "_Region", "_Category"]


def generate_sales(products, customers, tree, events, lifecycle, pricing_rules):
    all_dates = pd.date_range(START_DATE, END_DATE)
    years     = sorted(set(d.year for d in all_dates))

    year_factors, growths = build_year_factors(years)
    month_factors         = build_month_factors(years)
    promo_map             = build_promo_map()
    spike_map             = build_spike_map(all_dates)
    batch                 = BatchTracker(products["ProductKey"].tolist())
    engine                = DecisionEngine(tree, products, customers, lifecycle, pricing_rules)

    b2c_n = (customers["Segment"] == "B2C").sum()
    b2b_n = (customers["Segment"] == "B2B").sum()
    pl_n  = (customers["Country"] == "Polska").sum()

    print(f"\n{'='*58}")
    print(f"  TechMart FactSales Generator v{VERSION}")
    print(f"{'='*58}")
    print(f"  Zakres dat:    {START_DATE} – {END_DATE}")
    print(f"  Baza dzienna:  {BASE_DAILY_ORDERS} zamówień")
    print(f"\n  Wzrost rok do roku:")
    for y, f in year_factors.items():
        if y == years[0]:
            print(f"    {y}: baza (×{f:.3f})")
        else:
            print(f"    {y}: {growths[y]*100:+.1f}%  →  mnożnik ×{f:.3f}")
    print(f"\n  Klienci: {len(customers):,} łącznie")
    print(f"    B2C: {b2c_n:,} | B2B: {b2b_n:,}")
    print(f"    PL:  {pl_n:,} | Zagr: {len(customers)-pl_n:,}")

    if events:
        print(f"\n  Custom events: {len(events)} zdarzeń")
    if lifecycle:
        print(f"  Product lifecycle: {len(lifecycle)} produktów")
    print(f"  Pricing rules: cap {pricing_rules.get('cap', '?')}%, "
          f"{len(pricing_rules.get('aging_tiers', []))} aging tiers, "
          f"{len(pricing_rules.get('quantity_tiers', []))} qty tiers, "
          f"{len(pricing_rules.get('loyalty_tiers', []))} loyalty tiers")

    print(f"\n  Generowanie...", end="", flush=True)

    sales    = []
    order_id = 10000

    for d in all_dates:
        d_str = d.strftime("%Y-%m-%d")
        if d_str in POLISH_HOLIDAYS:
            continue

        y, m = d.year, d.month
        dow  = d.dayofweek + 1

        yf       = year_factors[y]
        mf       = month_factors[(y, m)]
        dowf     = DOW_BASE_PROFILE[dow] * (1 + np.random.normal(0, DOW_NOISE_SIGMA))
        eps      = np.random.lognormal(0, DAILY_LOGNORMAL_SIGMA)
        promo_b  = promo_map.get(d, 1.0)
        spike    = spike_map.get(d, 1.0)
        is_promo = d in promo_map

        n_orders = max(1, int(round(BASE_DAILY_ORDERS * yf * mf * dowf * eps * promo_b * spike)))

        active = get_active_events(events, d)

        day_sales = []
        for _ in range(n_orders):
            order_id += 1
            row = engine.generate_row(order_id, d_str, is_promo, batch, y, m, active)
            day_sales.append(row)

        if active:
            day_sales, order_id = apply_custom_events(
                day_sales, active, order_id,
                engine, batch, y, d_str, is_promo, m,
            )

        sales.extend(day_sales)

    print(" gotowe!")

    df = pd.DataFrame(sales)
    df.drop(columns=[c for c in _HIDDEN_COLS if c in df.columns], inplace=True)
    return df


def main():
    np.random.seed()

    dim_product, dim_customer = load_dimensions()
    tree          = load_decision_tree()
    events        = load_custom_events()
    lifecycle     = load_product_lifecycle()
    pricing_rules = load_pricing_rules()

    sales_df = generate_sales(dim_product, dim_customer, tree, events,
                               lifecycle, pricing_rules)
    print_summary(sales_df, dim_customer, dim_product)
    save_outputs(sales_df)
    print(f"\n  Gotowe!\n")


if __name__ == "__main__":
    main()
