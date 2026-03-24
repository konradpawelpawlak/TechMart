"""TechMart – Podsumowanie wygenerowanych danych"""

import pandas as pd


def print_summary(sales_df, customers, products):
    df = sales_df.copy()
    df["_year"] = pd.to_datetime(df["OrderDate"]).dt.year

    cust_map = customers.set_index("CustomerKey")[["Segment", "Country"]].to_dict("index")
    prod_map = products.set_index("ProductKey")[["Category", "UnitPrice_PLN", "CostPrice_PLN"]].to_dict("index")

    df["_Segment"]   = df["CustomerKey"].map(lambda k: cust_map.get(k, cust_map.get(str(k), {})).get("Segment", "?"))
    df["_Country"]   = df["CustomerKey"].map(lambda k: cust_map.get(k, cust_map.get(str(k), {})).get("Country", "?"))
    df["_Category"]  = df["ProductKey"].map(lambda k: prod_map.get(k, {}).get("Category", "?"))
    df["_UnitPrice"] = df["ProductKey"].map(lambda k: prod_map.get(k, {}).get("UnitPrice_PLN", 0))
    df["_CostPrice"] = df["ProductKey"].map(lambda k: prod_map.get(k, {}).get("CostPrice_PLN", 0))

    print(f"\n{'='*58}")
    print(f"  Podsumowanie")
    print(f"{'='*58}")
    print(f"  Laczna liczba wierszy: {len(df):,}")
    print(f"  Zakres dat: {df['OrderDate'].min()} – {df['OrderDate'].max()}")

    print(f"\n  Zamowienia per rok:")
    for y, cnt in df.groupby("_year").size().items():
        print(f"    {y}: {cnt:,}")

    print(f"\n  Podzial B2C / B2B (z DimCustomer):")
    for s, cnt in df["_Segment"].value_counts().items():
        print(f"    {s}: {cnt:,}  ({cnt/len(df)*100:.1f}%)")

    print(f"\n  Kanaly:")
    for ch, cnt in df["Channel"].value_counts().items():
        print(f"    {ch}: {cnt:,}  ({cnt/len(df)*100:.1f}%)")

    print(f"\n  Kategorie (z DimProduct):")
    for cat, cnt in df["_Category"].value_counts().items():
        print(f"    {cat}: {cnt:,}  ({cnt/len(df)*100:.1f}%)")

    print(f"\n  Kraje (z DimCustomer):")
    for c, cnt in df["_Country"].value_counts().items():
        print(f"    {c}: {cnt:,}  ({cnt/len(df)*100:.1f}%)")

    print(f"\n  Status zamowien:")
    for st, cnt in df["OrderStatus"].value_counts().items():
        print(f"    {st}: {cnt:,}  ({cnt/len(df)*100:.1f}%)")

    print(f"\n  Srednia qty per segment:")
    for seg in ["B2C", "B2B"]:
        subset = df[df["_Segment"] == seg]["Quantity"]
        if len(subset) > 0:
            print(f"    {seg}: {subset.mean():.2f} szt.")

    # --- Statystyki cen i rabatow ---
    print(f"\n  Rabaty:")
    print(f"    Sredni DiscountPct:   {df['DiscountPct'].mean():.2f}%")
    print(f"    Mediana DiscountPct:  {df['DiscountPct'].median():.1f}%")
    print(f"    Transakcje bez rabatu: {(df['DiscountPct'] == 0).sum():,}  ({(df['DiscountPct'] == 0).mean()*100:.1f}%)")
    print(f"    Transakcje z cap 40%: {(df['DiscountPct'] >= 40).sum():,}")

    print(f"\n  Ceny:")
    df["_Revenue"]  = df["UnitSalePrice"] * df["Quantity"]
    df["_Cost"]     = df["_CostPrice"] * df["Quantity"]
    df["_Margin"]   = df["_Revenue"] - df["_Cost"]

    total_rev  = df["_Revenue"].sum()
    total_cost = df["_Cost"].sum()
    total_marg = df["_Margin"].sum()
    loss_count = (df["_Margin"] < 0).sum()

    print(f"    Laczny przychod:     {total_rev:,.0f} PLN")
    print(f"    Laczny koszt:        {total_cost:,.0f} PLN")
    print(f"    Laczna marza:        {total_marg:,.0f} PLN ({total_marg/total_rev*100:.1f}%)")
    print(f"    Transakcje stratne:  {loss_count:,}  ({loss_count/len(df)*100:.1f}%)")

    print(f"\n  Marza per segment:")
    for seg in ["B2C", "B2B"]:
        s = df[df["_Segment"] == seg]
        if len(s) > 0:
            rev  = s["_Revenue"].sum()
            marg = s["_Margin"].sum()
            print(f"    {seg}: {marg:,.0f} PLN  ({marg/rev*100:.1f}% marzy)")

    print(f"\n  Metody platnosci:")
    for pm, cnt in df["PaymentMethod"].value_counts().items():
        print(f"    {pm}: {cnt:,}  ({cnt/len(df)*100:.1f}%)")

    print(f"\n  Sredni czas realizacji: {df['FulfillmentDays'].mean():.1f} dni")
    print(f"\n  Kolumny FactSales: {list(sales_df.columns)}")
