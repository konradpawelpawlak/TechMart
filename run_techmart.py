"""
TechMart – jeden program do pełnego generowania (DimCustomer → FactSales).
Punkt wejścia pod PyInstaller (.exe bez instalacji Pythona).
"""

from __future__ import annotations


def main() -> None:
    print("\n  === TechMart: krok 1/2 – DimCustomer ===\n")
    from generate_dim_customer import main as gen_customers

    gen_customers()

    print("\n  === TechMart: krok 2/2 – FactSales ===\n")
    from generate_fact_sales import main as gen_sales

    gen_sales()

    out_dir_msg = (
        "Pliki DimCustomer.csv i FactSales.csv zapisano w tym samym folderze co program."
    )
    print(f"\n  {out_dir_msg}\n")


if __name__ == "__main__":
    main()
