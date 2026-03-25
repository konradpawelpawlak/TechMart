"""TechMart – Zapis wyników do CSV"""

from techmart.config import OUTPUT_CSV
from techmart.loaders import output_path


def save_outputs(sales_df):
    sales_df.to_csv(output_path(OUTPUT_CSV), index=False)
    print(f"\n  ✓ {OUTPUT_CSV}")
