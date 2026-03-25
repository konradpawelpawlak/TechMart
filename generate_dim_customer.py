"""
TechMart – Generator klientów (DimCustomer)
=============================================
Tworzy tabelę DimCustomer.csv z realistycznymi identyfikatorami:
    B2B → NIP/tax ID w formacie danego kraju
        PL: PL762-14-67-909  (PL + 10 cyfr z myślnikami)
        DE: DE123456789       (DE + 9 cyfr)
        CZ: CZ12345678        (CZ + 8-10 cyfr)
        SK: SK1234567890      (SK + 10 cyfr)
    B2C → numer sekwencyjny: 1, 2, 3, ...

Korzysta z decision_tree.json do losowania Country i Region.

Uruchomienie:
    python generate_dim_customer.py

Wyjście:
    DimCustomer.csv
"""

import os

import numpy as np
import pandas as pd

from techmart.loaders import load_decision_tree, output_path, resource_path

# ============================================================
#  CONFIG
# ============================================================

TARGET_B2C_COUNT = 10000
TARGET_B2B_COUNT = 200

OUTPUT_FILE        = "DimCustomer.csv"
NAMES_FILE         = "imiona_i_nazwiska_lista.csv"

# Nazwy firm — pule do losowania nazw B2B
B2B_PREFIXES_PL = [
    "Tech", "Info", "Data", "Cyber", "Net", "Digi", "Smart", "Pro",
    "Euro", "Pol", "Trans", "Mega", "Global", "Inter", "Eko", "Nowa",
]
B2B_SUFFIXES_PL = [
    "Systems", "Serwis", "Group", "Handel", "Solutions", "Logistics",
    "Consulting", "Polska", "Partners", "Invest", "Bud", "Expo",
]
B2B_PREFIXES_DE = [
    "Tech", "Info", "Daten", "Digital", "Nord", "Süd", "Rhein", "Bau",
    "Werk", "Kraft", "Stern", "Blitz", "Schnell", "Grün", "Neu",
]
B2B_SUFFIXES_DE = [
    "GmbH", "AG", "Solutions", "Technik", "Handel", "Systeme",
    "Dienst", "Werk", "Logistik", "Beratung",
]
B2B_PREFIXES_CZ = [
    "Tech", "Info", "Data", "Digi", "Prag", "Česk", "Smart", "Nový",
    "Rychl", "Modr", "Zelen", "Velk",
]
B2B_SUFFIXES_CZ = [
    "s.r.o.", "a.s.", "Systems", "Služby", "Technika", "Obchod",
    "Řešení", "Logistika",
]
B2B_PREFIXES_SK = [
    "Tech", "Info", "Dáta", "Digi", "Brati", "Slovák", "Smart", "Nový",
    "Rýchl", "Modr", "Zelen", "Veľk",
]
B2B_SUFFIXES_SK = [
    "s.r.o.", "a.s.", "Systems", "Služby", "Technika", "Obchod",
    "Riešenia", "Logistika",
]

B2B_NAME_POOLS = {
    "Polska":   (B2B_PREFIXES_PL, B2B_SUFFIXES_PL),
    "Niemcy":   (B2B_PREFIXES_DE, B2B_SUFFIXES_DE),
    "Czechy":   (B2B_PREFIXES_CZ, B2B_SUFFIXES_CZ),
    "Słowacja": (B2B_PREFIXES_SK, B2B_SUFFIXES_SK),
}

# Imiona i nazwiska PL — ładowane z pliku CSV z częstotliwościami
# Struktura: wartość, ilość, płeć (K/M), typ (imię/nazwisko), szansa (%)
# Ładowane w load_polish_names()

FIRST_NAMES_DE = [
    "Thomas", "Anna", "Michael", "Julia", "Stefan", "Sabine", "Andreas",
    "Claudia", "Martin", "Petra", "Klaus", "Monika", "Wolfgang", "Ursula",
    "Hans", "Maria", "Peter", "Christine", "Frank", "Katharina",
    "Lukas", "Sophie", "Felix", "Lena", "Maximilian", "Emma",
]
LAST_NAMES_DE = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer",
    "Wagner", "Becker", "Schulz", "Hoffmann", "Schäfer", "Koch",
    "Bauer", "Richter", "Klein", "Wolf", "Schröder", "Neumann",
    "Schwarz", "Zimmermann", "Braun", "Krüger", "Hofmann", "Hartmann",
]
FIRST_NAMES_CZ = [
    "Jan", "Jana", "Petr", "Eva", "Martin", "Marie", "Tomáš", "Lucie",
    "Pavel", "Kateřina", "Jakub", "Tereza", "Ondřej", "Anna", "David", "Hana",
]
LAST_NAMES_CZ = [
    "Novák", "Svoboda", "Novotný", "Dvořák", "Černý", "Procházka",
    "Kučera", "Veselý", "Horák", "Němec", "Pokorný", "Marek",
    "Pospíšil", "Hájek", "Jelínek", "Král",
]
FIRST_NAMES_SK = [
    "Ján", "Mária", "Peter", "Anna", "Martin", "Eva", "Tomáš", "Katarína",
    "Marek", "Zuzana", "Michal", "Monika", "Lukáš", "Jana", "Dávid", "Martina",
]
LAST_NAMES_SK = [
    "Horváth", "Kováč", "Varga", "Tóth", "Nagy", "Baláž", "Molnár",
    "Szabó", "Novák", "Černák", "Polák", "Kráľ", "Lukáč", "Hudák",
]

NAME_POOLS_FOREIGN = {
    "Niemcy":   (FIRST_NAMES_DE, LAST_NAMES_DE),
    "Czechy":   (FIRST_NAMES_CZ, LAST_NAMES_CZ),
    "Słowacja": (FIRST_NAMES_SK, LAST_NAMES_SK),
}

# Cache for Polish names loaded from file
_PL_NAMES_CACHE = None


def load_polish_names():
    """
    Ładuje imiona i nazwiska z pliku CSV.
    Zwraca dict z 4 kluczami: imiona_K, imiona_M, nazwiska_K, nazwiska_M.
    Każdy to tuple (values, probs) do użycia z np.random.choice.
    """
    global _PL_NAMES_CACHE
    if _PL_NAMES_CACHE is not None:
        return _PL_NAMES_CACHE

    path = resource_path(NAMES_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Nie znaleziono pliku z imionami: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig", usecols=["wartość", "płeć", "typ", "szansa"])
    df["szansa_num"] = df["szansa"].str.replace("%", "").str.replace(",", ".").astype(float)

    result = {}
    for gender in ["K", "M"]:
        for typ in ["imię", "nazwisko"]:
            subset = df[(df["płeć"] == gender) & (df["typ"] == typ)].copy()
            values = subset["wartość"].tolist()
            probs  = subset["szansa_num"].values.astype(float)
            probs  = probs / probs.sum()
            key    = f"{'imiona' if typ == 'imię' else 'nazwiska'}_{gender}"
            result[key] = (values, probs)

    _PL_NAMES_CACHE = result
    print(f"    Załadowano PL: {len(result['imiona_K'][0])} imion K, "
          f"{len(result['imiona_M'][0])} imion M, "
          f"{len(result['nazwiska_K'][0])} nazwisk K, "
          f"{len(result['nazwiska_M'][0])} nazwisk M")
    return result


def generate_pl_name():
    """Losuje polskie imię + nazwisko z uwzględnieniem płci i częstotliwości."""
    names = load_polish_names()
    gender = np.random.choice(["K", "M"])
    first_vals, first_probs = names[f"imiona_{gender}"]
    last_vals, last_probs   = names[f"nazwiska_{gender}"]
    first = np.random.choice(first_vals, p=first_probs)
    last  = np.random.choice(last_vals, p=last_probs)
    return f"{first} {last}"


# ============================================================
#  POMOCNICZE
# ============================================================

def weighted_choice(prob_dict):
    keys    = list(prob_dict.keys())
    weights = np.array([prob_dict[k] for k in keys], dtype=float)
    weights /= weights.sum()
    return keys[np.random.choice(len(keys), p=weights)]


# ============================================================
#  GENEROWANIE IDENTYFIKATORÓW
# ============================================================

def generate_nip_pl():
    """PL + 10 cyfr z myślnikami: PL762-14-67-909"""
    d = [np.random.randint(0, 10) for _ in range(10)]
    return f"PL{''.join(map(str, d[:3]))}-{''.join(map(str, d[3:5]))}-{''.join(map(str, d[5:7]))}-{''.join(map(str, d[7:10]))}"


def generate_ust_de():
    """DE + 9 cyfr: DE123456789"""
    d = [np.random.randint(0, 10) for _ in range(9)]
    return f"DE{''.join(map(str, d))}"


def generate_dic_cz():
    """CZ + 8-10 cyfr: CZ12345678"""
    length = np.random.choice([8, 9, 10])
    d = [np.random.randint(0, 10) for _ in range(length)]
    return f"CZ{''.join(map(str, d))}"


def generate_ic_sk():
    """SK + 10 cyfr: SK1234567890"""
    d = [np.random.randint(0, 10) for _ in range(10)]
    return f"SK{''.join(map(str, d))}"


TAX_ID_GENERATORS = {
    "Polska":   generate_nip_pl,
    "Niemcy":   generate_ust_de,
    "Czechy":   generate_dic_cz,
    "Słowacja": generate_ic_sk,
}


# ============================================================
#  GENEROWANIE KLIENTÓW
# ============================================================

def generate_b2b_customer(country, region, used_ids):
    """Generuje jednego klienta B2B z NIP-em i nazwą firmy."""
    # unikalne ID
    gen = TAX_ID_GENERATORS[country]
    cust_id = gen()
    while cust_id in used_ids:
        cust_id = gen()
    used_ids.add(cust_id)

    # nazwa firmy
    prefixes, suffixes = B2B_NAME_POOLS.get(country, (B2B_PREFIXES_PL, B2B_SUFFIXES_PL))
    name = f"{np.random.choice(prefixes)}{np.random.choice(suffixes)}"

    return {
        "CustomerKey": cust_id,
        "CustomerName": name,
        "Segment":      "B2B",
        "Country":      country,
        "Region":       region,
    }


def generate_b2c_customer(seq_id, country, region):
    """Generuje jednego klienta B2C z numerem sekwencyjnym i imieniem+nazwiskiem."""
    if country == "Polska":
        name = generate_pl_name()
    else:
        firsts, lasts = NAME_POOLS_FOREIGN.get(country, (FIRST_NAMES_DE, LAST_NAMES_DE))
        name = f"{np.random.choice(firsts)} {np.random.choice(lasts)}"

    return {
        "CustomerKey": seq_id,
        "CustomerName": name,
        "Segment":      "B2C",
        "Country":      country,
        "Region":       region,
    }


def generate_customers():
    tree = load_decision_tree()

    customers = []
    used_b2b_ids = set()

    # --- B2B ---
    print(f"  Generowanie B2B: {TARGET_B2B_COUNT} klientów...", end="", flush=True)
    for _ in range(TARGET_B2B_COUNT):
        country = weighted_choice(tree["country"]["B2B"])
        if country == "Polska" and country in tree["region"]:
            region = weighted_choice(tree["region"][country])
        else:
            region = None
        customers.append(generate_b2b_customer(country, region, used_b2b_ids))
    print(" OK")

    # --- B2C ---
    print(f"  Generowanie B2C: {TARGET_B2C_COUNT} klientów...", end="", flush=True)
    for i in range(1, TARGET_B2C_COUNT + 1):
        country = weighted_choice(tree["country"]["B2C"])
        if country == "Polska" and country in tree["region"]:
            region = weighted_choice(tree["region"][country])
        else:
            region = None
        customers.append(generate_b2c_customer(i, country, region))
    print(" OK")

    return pd.DataFrame(customers)


# ============================================================
#  PODSUMOWANIE
# ============================================================

def print_summary(df):
    print(f"\n{'='*54}")
    print(f"  DimCustomer – Podsumowanie")
    print(f"{'='*54}")
    print(f"  Łącznie: {len(df):,} klientów")

    print(f"\n  Segment:")
    for s, cnt in df["Segment"].value_counts().items():
        print(f"    {s}: {cnt:,}")

    print(f"\n  Kraj:")
    for c, cnt in df["Country"].value_counts().items():
        print(f"    {c}: {cnt:,}  ({cnt/len(df)*100:.1f}%)")

    print(f"\n  Top 5 regionów (PL):")
    pl_regions = df[df["Country"] == "Polska"]["Region"].value_counts().head(5)
    for r, cnt in pl_regions.items():
        print(f"    {r}: {cnt:,}")

    print(f"\n  Przykładowe CustomerKey B2B:")
    b2b = df[df["Segment"] == "B2B"].head(5)
    for _, row in b2b.iterrows():
        print(f"    {row['CustomerKey']}  {row['CustomerName']}  ({row['Country']})")

    print(f"\n  Przykładowe CustomerKey B2C:")
    b2c = df[df["Segment"] == "B2C"].head(5)
    for _, row in b2c.iterrows():
        print(f"    {row['CustomerKey']}  {row['CustomerName']}  ({row['Country']})")


# ============================================================
#  ENTRY POINT
# ============================================================

def main():
    np.random.seed()

    print(f"\n{'='*54}")
    print(f"  TechMart – Generator DimCustomer")
    print(f"{'='*54}")

    df = generate_customers()
    print_summary(df)

    out = output_path(OUTPUT_FILE)
    df.to_csv(out, index=False)
    print(f"\n  ✓ {OUTPUT_FILE}  ({len(df):,} wierszy)")
    print(f"  Gotowe!\n")


if __name__ == "__main__":
    main()
