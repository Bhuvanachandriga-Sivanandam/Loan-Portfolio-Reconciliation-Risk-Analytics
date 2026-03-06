"""
Output Validation Script
Cross-checks Alteryx workflow outputs against expected results.
Run this after completing all workflows to verify accuracy.

Author: Bhuvanachandriga
"""

import csv
import os
from collections import Counter
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


def load_csv(filepath):
    with open(filepath, "r") as f:
        return list(csv.DictReader(f))


def validate_data_quality():
    """Check that data quality exceptions were properly identified."""
    print("=" * 60)
    print("VALIDATION 1: Data Quality Checks")
    print("=" * 60)

    cbs = load_csv(RAW_DIR / "loans_cbs.csv")
    los = load_csv(RAW_DIR / "loans_los.csv")

    # Check for negative balances
    neg_bal_cbs = sum(1 for r in cbs if float(r["current_balance"]) < 0)
    neg_bal_los = sum(1 for r in los if float(r["current_balance"]) < 0)
    print(f"  Negative balances — CBS: {neg_bal_cbs}, LOS: {neg_bal_los}")

    # Check for missing loan IDs
    missing_id_cbs = sum(1 for r in cbs if not r.get("loan_id", "").strip())
    missing_id_los = sum(1 for r in los if not r.get("loan_id", "").strip())
    print(f"  Missing loan IDs — CBS: {missing_id_cbs}, LOS: {missing_id_los}")

    # Check for rate outliers
    rate_outliers_cbs = sum(1 for r in cbs if float(r["interest_rate"]) > 30 or float(r["interest_rate"]) < 0)
    print(f"  Rate outliers (CBS): {rate_outliers_cbs}")

    # Check LOS date format inconsistencies
    mixed_dates = sum(1 for r in los if "/" in r.get("origination_date", ""))
    print(f"  LOS date format inconsistencies (MM/DD/YYYY): {mixed_dates}")

    # Check name casing issues
    upper_names = sum(1 for r in los if r.get("customer_name", "") == r.get("customer_name", "").upper()
                      and len(r.get("customer_name", "")) > 2)
    lower_names = sum(1 for r in los if r.get("customer_name", "") == r.get("customer_name", "").lower()
                      and len(r.get("customer_name", "")) > 2)
    print(f"  Name casing issues — ALL CAPS: {upper_names}, all lower: {lower_names}")
    print()


def validate_reconciliation():
    """Verify reconciliation counts and discrepancy detection."""
    print("=" * 60)
    print("VALIDATION 2: Reconciliation Accuracy")
    print("=" * 60)

    cbs = load_csv(RAW_DIR / "loans_cbs.csv")
    los = load_csv(RAW_DIR / "loans_los.csv")

    cbs_ids = {r["loan_id"] for r in cbs}
    los_ids = {r["loan_id"] for r in los}

    matched = cbs_ids & los_ids
    cbs_only = cbs_ids - los_ids
    los_only = los_ids - cbs_ids

    print(f"  CBS records: {len(cbs_ids)}")
    print(f"  LOS records: {len(los_ids)}")
    print(f"  Matched loan IDs: {len(matched)}")
    print(f"  CBS-only orphans: {len(cbs_only)}")
    print(f"  LOS-only orphans: {len(los_only)}")

    # Build lookup maps for balance comparison
    cbs_map = {r["loan_id"]: r for r in cbs}
    los_map = {r["loan_id"]: r for r in los}

    exact = tolerance = soft = hard = 0
    total_variance = 0

    for lid in matched:
        cbs_bal = float(cbs_map[lid]["current_balance"])
        los_bal = float(los_map[lid]["current_balance"])
        cbs_rate = float(cbs_map[lid]["interest_rate"])
        los_rate = float(los_map[lid]["interest_rate"])

        bal_var = abs(cbs_bal - los_bal)
        rate_var = abs(cbs_rate - los_rate)
        total_variance += bal_var

        if bal_var == 0 and rate_var == 0:
            exact += 1
        elif bal_var <= 50 and rate_var <= 0.0005:
            tolerance += 1
        elif bal_var <= 500:
            soft += 1
        else:
            hard += 1

    print(f"\n  Match classification (Python validation):")
    print(f"    Exact Match:      {exact:>5} ({exact/len(matched)*100:.1f}%)")
    print(f"    Tolerance Match:  {tolerance:>5} ({tolerance/len(matched)*100:.1f}%)")
    print(f"    Soft Break:       {soft:>5} ({soft/len(matched)*100:.1f}%)")
    print(f"    Hard Break:       {hard:>5} ({hard/len(matched)*100:.1f}%)")
    print(f"    Total variance:   ${total_variance:,.2f}")
    print()


def validate_portfolio_stats():
    """Basic portfolio statistics for sanity check."""
    print("=" * 60)
    print("VALIDATION 3: Portfolio Statistics")
    print("=" * 60)

    los = load_csv(RAW_DIR / "loans_los.csv")

    # Product distribution
    products = Counter(r["product_code"] for r in los)
    total_balance = sum(float(r["current_balance"]) for r in los)

    print(f"  Total loans: {len(los)}")
    print(f"  Total portfolio balance: ${total_balance:,.2f}")
    print(f"\n  Product distribution:")
    for prod, count in products.most_common():
        prod_balance = sum(float(r["current_balance"]) for r in los if r["product_code"] == prod)
        print(f"    {prod:<10} {count:>5} loans  ${prod_balance:>14,.2f}  ({prod_balance/total_balance*100:.1f}%)")

    # Province distribution
    provinces = Counter(r.get("province", "N/A") for r in los)
    print(f"\n  Geographic distribution:")
    for prov, count in provinces.most_common():
        print(f"    {prov:<5} {count:>5} loans ({count/len(los)*100:.1f}%)")

    # Risk grade distribution
    grades = Counter(r.get("risk_grade", "N/A") for r in los)
    print(f"\n  Risk grade distribution:")
    for grade in ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]:
        count = grades.get(grade, 0)
        print(f"    {grade:<5} {count:>5} loans ({count/len(los)*100:.1f}%)")

    print()


def main():
    print("\n" + "=" * 60)
    print("  LOAN PORTFOLIO RECONCILIATION — OUTPUT VALIDATION")
    print("=" * 60 + "\n")

    if not (RAW_DIR / "loans_cbs.csv").exists():
        print("ERROR: Raw data files not found. Run generate_sample_data.py first.")
        return

    validate_data_quality()
    validate_reconciliation()
    validate_portfolio_stats()

    print("=" * 60)
    print("  Validation complete. Compare these numbers against")
    print("  your Alteryx workflow outputs to verify accuracy.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
