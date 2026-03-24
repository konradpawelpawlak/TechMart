"""TechMart – Dzienne faktory (sezonowość, wzrost, spiki, promocje)"""

import numpy as np
import pandas as pd

from techmart.config import (
    YEAR_GROWTH_MU, YEAR_GROWTH_SIGMA,
    MONTH_BASE_PROFILE, MONTH_NOISE_SIGMA,
    SPIKE_COUNT_PER_YEAR, SPIKE_MULT_MIN, SPIKE_MULT_MAX,
    DIP_COUNT_PER_YEAR, DIP_MULT_MIN, DIP_MULT_MAX,
    PROMO_BOOST_MIN, PROMO_BOOST_MAX, PROMOTION_DATES,
)


def build_year_factors(years):
    factors, growths = {}, {}
    current = 1.0
    for i, y in enumerate(years):
        if i == 0:
            factors[y] = 1.0
        else:
            g          = np.random.normal(YEAR_GROWTH_MU, YEAR_GROWTH_SIGMA)
            current   *= (1 + g)
            factors[y] = current
            growths[y] = g
    return factors, growths


def build_month_factors(years):
    factors = {}
    for y in years:
        for m in range(1, 13):
            sigma          = MONTH_NOISE_SIGMA[m] if isinstance(MONTH_NOISE_SIGMA, dict) else MONTH_NOISE_SIGMA
            noise          = np.random.normal(0, sigma)
            factors[(y,m)] = max(0.15, MONTH_BASE_PROFILE[m] * (1 + noise))
    return factors


def build_promo_map():
    promo_map = {}
    for start, end in PROMOTION_DATES:
        boost = np.random.uniform(PROMO_BOOST_MIN, PROMO_BOOST_MAX)
        for d in pd.date_range(start, end):
            promo_map[d] = boost
    return promo_map


def build_spike_map(dates):
    spike_map    = {}
    years        = sorted(set(d.year for d in dates))
    days_by_year = {y: [d for d in dates if d.year == y] for y in years}
    for y, days in days_by_year.items():
        spike_days = np.random.choice(days, size=min(SPIKE_COUNT_PER_YEAR, len(days)), replace=False)
        for d in spike_days:
            spike_map[pd.Timestamp(d)] = np.random.uniform(SPIKE_MULT_MIN, SPIKE_MULT_MAX)
        remaining = [d for d in days if pd.Timestamp(d) not in spike_map]
        dip_days  = np.random.choice(remaining, size=min(DIP_COUNT_PER_YEAR, len(remaining)), replace=False)
        for d in dip_days:
            spike_map[pd.Timestamp(d)] = np.random.uniform(DIP_MULT_MIN, DIP_MULT_MAX)
    return spike_map
