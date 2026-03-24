"""TechMart – Konfiguracja generatora v10"""

VERSION = "11"

# --- Zakres dat ---
START_DATE = "2021-01-01"
END_DATE   = "2024-12-31"

# --- Skala ---
BASE_DAILY_ORDERS = 20

# --- Wzrost rok do roku ---
YEAR_GROWTH_MU    = 0.12
YEAR_GROWTH_SIGMA = 0.10

# --- Sezonowość miesięczna ---
MONTH_BASE_PROFILE = {
    1: 0.72, 2: 0.68, 3: 0.74, 4: 0.80, 5: 0.86, 6: 1.11,
    7: 0.42, 8: 0.45, 9: 0.94, 10: 1.00, 11: 1.90, 12: 2.60
}
MONTH_NOISE_SIGMA = {
    1: 0.10, 2: 0.10, 3: 0.48, 4: 0.52, 5: 0.47, 6: 0.10,
    7: 0.10, 8: 0.10, 9: 0.10, 10: 0.10, 11: 0.12, 12: 0.27
}

# --- Sezonowość tygodniowa ---
DOW_BASE_PROFILE = {
    1: 0.78, 2: 0.83, 3: 0.89, 4: 0.94,
    5: 1.32, 6: 1.38, 7: 0.62
}
DOW_NOISE_SIGMA = 0.05

# --- Dzienny szum losowy ---
DAILY_LOGNORMAL_SIGMA = 0.20

# --- Jednorazowe spiki / dołki ---
SPIKE_COUNT_PER_YEAR = 4
SPIKE_MULT_MIN       = 1.8
SPIKE_MULT_MAX       = 3.5
DIP_COUNT_PER_YEAR   = 3
DIP_MULT_MIN         = 0.10
DIP_MULT_MAX         = 0.40

# --- Promocje ---
PROMO_BOOST_MIN = 1.3
PROMO_BOOST_MAX = 2.4
PROMOTION_DATES = [
    ("2021-08-20", "2021-09-10"), ("2021-11-26", "2021-11-28"),
    ("2021-12-20", "2021-12-31"), ("2022-07-01", "2022-07-31"),
    ("2022-08-20", "2022-09-10"), ("2022-11-25", "2022-11-27"),
    ("2022-12-19", "2022-12-31"), ("2023-07-01", "2023-07-31"),
    ("2023-08-20", "2023-09-10"), ("2023-11-24", "2023-11-26"),
    ("2023-12-18", "2023-12-31"), ("2024-07-01", "2024-07-31"),
    ("2024-08-19", "2024-09-08"), ("2024-11-29", "2024-12-01"),
    ("2024-12-16", "2024-12-31"),
]

# --- Polskie święta (brak sprzedaży) ---
POLISH_HOLIDAYS = {
    "2021-01-01","2021-04-04","2021-04-05","2021-05-01","2021-05-03",
    "2021-06-03","2021-06-20","2021-08-15","2021-11-01","2021-11-11",
    "2021-12-25","2021-12-26",
    "2022-01-01","2022-04-17","2022-04-18","2022-05-01","2022-05-03",
    "2022-06-16","2022-06-23","2022-08-15","2022-11-01","2022-11-11",
    "2022-12-25","2022-12-26",
    "2023-01-01","2023-04-09","2023-04-10","2023-05-01","2023-05-03",
    "2023-06-08","2023-06-15","2023-08-15","2023-11-01","2023-11-11",
    "2023-12-25","2023-12-26",
    "2024-01-01","2024-03-31","2024-04-01","2024-05-01","2024-05-03",
    "2024-05-19","2024-05-30","2024-08-15","2024-11-01","2024-11-11",
    "2024-12-25","2024-12-26",
}

# --- Partie produktów ---
BATCH_SIZE = 200

# --- Pliki ---
OUTPUT_CSV              = "FactSales.csv"
DIM_PRODUCT_FILE        = "DimProduct.csv"
DIM_CUSTOMER_FILE       = "DimCustomer.csv"
DECISION_TREE_FILE      = "decision_tree.json"
CUSTOM_EVENTS_FILE      = "custom_events.json"
PRODUCT_LIFECYCLE_FILE  = "product_lifecycle.json"
PRICING_RULES_FILE      = "pricing_rules.json"
