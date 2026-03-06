"""
Synthetic Loan Portfolio Data Generator
Generates realistic multi-source banking data with intentionally seeded discrepancies
for reconciliation analytics demonstration.

Author: Bhuvanachandriga
"""

import csv
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

# ─── Configuration ────────────────────────────────────────────────────────────

NUM_LOANS = 5000
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"

PROVINCES = ["ON", "BC", "AB", "QC", "MB", "SK", "NS", "NB"]
PROVINCE_WEIGHTS = [0.40, 0.18, 0.15, 0.12, 0.05, 0.04, 0.03, 0.03]

PRODUCTS = [
    {"code": "MTG-FIX", "name": "Fixed Rate Mortgage", "min_amount": 100000, "max_amount": 800000, "min_rate": 4.5, "max_rate": 6.5, "term_months": 300},
    {"code": "MTG-VAR", "name": "Variable Rate Mortgage", "min_amount": 100000, "max_amount": 700000, "min_rate": 5.0, "max_rate": 7.0, "term_months": 300},
    {"code": "HELOC", "name": "Home Equity Line of Credit", "min_amount": 25000, "max_amount": 300000, "min_rate": 6.0, "max_rate": 8.5, "term_months": 120},
    {"code": "AUTO", "name": "Auto Loan", "min_amount": 10000, "max_amount": 75000, "min_rate": 5.5, "max_rate": 9.0, "term_months": 72},
    {"code": "PL-SEC", "name": "Secured Personal Loan", "min_amount": 5000, "max_amount": 50000, "min_rate": 7.0, "max_rate": 12.0, "term_months": 60},
    {"code": "PL-UNSEC", "name": "Unsecured Personal Loan", "min_amount": 2000, "max_amount": 35000, "min_rate": 8.5, "max_rate": 15.0, "term_months": 48},
    {"code": "LOC", "name": "Line of Credit", "min_amount": 5000, "max_amount": 50000, "min_rate": 7.5, "max_rate": 12.5, "term_months": 60},
    {"code": "STUDENT", "name": "Student Loan", "min_amount": 5000, "max_amount": 60000, "min_rate": 4.0, "max_rate": 7.5, "term_months": 120},
]
PRODUCT_WEIGHTS = [0.25, 0.15, 0.10, 0.15, 0.10, 0.10, 0.08, 0.07]

RISK_GRADES = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
RISK_WEIGHTS = [0.05, 0.15, 0.25, 0.25, 0.15, 0.10, 0.05]

STATUSES = ["Active", "Delinquent-30", "Delinquent-60", "Delinquent-90", "Default", "Closed", "Restructured"]
STATUS_WEIGHTS = [0.72, 0.08, 0.05, 0.03, 0.02, 0.07, 0.03]

BRANCHES = [f"BR-{str(i).zfill(3)}" for i in range(1, 26)]

FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "David", "Linda",
               "William", "Elizabeth", "Richard", "Barbara", "Joseph", "Susan", "Thomas", "Jessica",
               "Sarah", "Karen", "Nancy", "Lisa", "Margaret", "Sandra", "Ashley", "Donna",
               "Priya", "Wei", "Fatima", "Mohammed", "Yuki", "Carlos", "Amara", "Raj"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
              "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
              "Taylor", "Moore", "Jackson", "Martin", "Lee", "Patel", "Kim", "Singh", "Chen",
              "Nguyen", "Santos", "Sharma", "Ahmed", "Ali", "Das"]


# ─── Helper Functions ─────────────────────────────────────────────────────────

def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def _calc_payment(balance, annual_rate, remaining_months):
    """Calculate monthly payment safely."""
    if balance <= 0 or annual_rate <= 0 or remaining_months <= 0:
        return 0
    r = annual_rate / 100 / 12
    denom = 1 - (1 + r) ** (-remaining_months)
    if abs(denom) < 1e-10:
        return 0
    return balance * r / denom


def random_date(start_year=2019, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 6, 30)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_loan_id(index):
    return f"LN-{str(index).zfill(7)}"


def generate_customer_id(index):
    return f"CUST-{str(index).zfill(6)}"


# ─── Data Generation ──────────────────────────────────────────────────────────

def generate_base_loans():
    """Generate the base loan records that both systems should agree on."""
    loans = []
    customer_pool_size = int(NUM_LOANS * 0.85)  # some customers have multiple loans

    for i in range(1, NUM_LOANS + 1):
        product = weighted_choice(PRODUCTS, PRODUCT_WEIGHTS)
        province = weighted_choice(PROVINCES, PROVINCE_WEIGHTS)
        risk_grade = weighted_choice(RISK_GRADES, RISK_WEIGHTS)
        status = weighted_choice(STATUSES, STATUS_WEIGHTS)
        origination_date = random_date()

        original_amount = round(random.uniform(product["min_amount"], product["max_amount"]), 2)
        interest_rate = round(random.uniform(product["min_rate"], product["max_rate"]), 4)

        # Calculate current balance based on age and status
        months_elapsed = (datetime(2025, 9, 1) - origination_date).days / 30
        if status == "Closed":
            current_balance = 0
        else:
            paydown_factor = max(0.1, 1 - (months_elapsed / product["term_months"]))
            current_balance = round(original_amount * paydown_factor * random.uniform(0.85, 1.05), 2)

        # Days past due
        dpd_map = {"Active": 0, "Delinquent-30": random.randint(30, 59),
                    "Delinquent-60": random.randint(60, 89), "Delinquent-90": random.randint(90, 179),
                    "Default": random.randint(180, 365), "Closed": 0,
                    "Restructured": random.randint(0, 30)}
        days_past_due = dpd_map.get(status, 0)

        # Credit score
        base_score = {"AAA": 820, "AA": 780, "A": 740, "BBB": 700, "BB": 650, "B": 600, "CCC": 550}
        credit_score = base_score[risk_grade] + random.randint(-30, 30)
        credit_score = max(300, min(900, credit_score))

        # LTV for secured products
        if product["code"] in ["MTG-FIX", "MTG-VAR", "HELOC"]:
            property_value = original_amount / random.uniform(0.55, 0.90)
            ltv = round(current_balance / property_value * 100, 2) if property_value > 0 else 0
        else:
            property_value = 0
            ltv = 0

        customer_idx = random.randint(1, customer_pool_size)

        loan = {
            "loan_id": generate_loan_id(i),
            "customer_id": generate_customer_id(customer_idx),
            "customer_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "product_code": product["code"],
            "product_name": product["name"],
            "province": province,
            "branch_id": random.choice(BRANCHES),
            "origination_date": origination_date.strftime("%Y-%m-%d"),
            "maturity_date": (origination_date + timedelta(days=product["term_months"] * 30)).strftime("%Y-%m-%d"),
            "original_amount": original_amount,
            "current_balance": current_balance,
            "interest_rate": interest_rate,
            "risk_grade": risk_grade,
            "status": status,
            "days_past_due": days_past_due,
            "credit_score": credit_score,
            "property_value": round(property_value, 2),
            "ltv_ratio": ltv,
            "monthly_payment": round(_calc_payment(current_balance, interest_rate, max(1, product["term_months"] - int(months_elapsed))), 2),
        }
        loans.append(loan)

    return loans


def write_cbs_extract(loans):
    """Core Banking System extract — the 'source of truth' for balances."""
    filepath = OUTPUT_DIR / "loans_cbs.csv"
    fields = ["loan_id", "customer_id", "product_code", "branch_id", "origination_date",
              "current_balance", "interest_rate", "status", "days_past_due",
              "last_payment_date", "next_payment_date", "monthly_payment"]

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for i, loan in enumerate(loans):
            row = {k: loan[k] for k in fields if k in loan}

            # Add CBS-specific fields
            orig = datetime.strptime(loan["origination_date"], "%Y-%m-%d")
            row["last_payment_date"] = (datetime(2025, 8, 15) - timedelta(days=random.randint(1, 35))).strftime("%Y-%m-%d")
            row["next_payment_date"] = (datetime(2025, 9, 15) + timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d")

            # ── SEED DISCREPANCIES ──
            # ~3% balance mismatches (posting errors, timing differences)
            if random.random() < 0.03:
                variance = random.choice([
                    random.uniform(50, 500),       # small posting error
                    random.uniform(500, 5000),      # medium sync issue
                    random.uniform(5000, 50000),    # large discrepancy
                ])
                row["current_balance"] = round(loan["current_balance"] + random.choice([-1, 1]) * variance, 2)

            # ~1.5% rate discrepancies
            if random.random() < 0.015:
                row["interest_rate"] = round(loan["interest_rate"] + random.uniform(-0.5, 0.5), 4)

            # ~0.5% status mismatches (CBS shows different status)
            if random.random() < 0.005:
                row["status"] = random.choice(["Active", "Delinquent-30", "Restructured"])

            writer.writerow(row)

    # Add ~1% orphan records (exist in CBS but not LOS)
    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        for i in range(NUM_LOANS + 1, NUM_LOANS + 51):
            product = random.choice(PRODUCTS)
            writer.writerow({
                "loan_id": generate_loan_id(i),
                "customer_id": generate_customer_id(random.randint(1, 4000)),
                "product_code": product["code"],
                "branch_id": random.choice(BRANCHES),
                "origination_date": random_date(2023, 2025).strftime("%Y-%m-%d"),
                "current_balance": round(random.uniform(5000, 200000), 2),
                "interest_rate": round(random.uniform(product["min_rate"], product["max_rate"]), 4),
                "status": "Active",
                "days_past_due": 0,
                "last_payment_date": "2025-08-10",
                "next_payment_date": "2025-09-10",
                "monthly_payment": round(random.uniform(200, 3000), 2),
            })

    print(f"  CBS extract: {filepath}")


def write_los_extract(loans):
    """Loan Origination System extract — application and approval data."""
    filepath = OUTPUT_DIR / "loans_los.csv"
    fields = ["loan_id", "customer_id", "customer_name", "product_code", "product_name",
              "province", "branch_id", "origination_date", "maturity_date",
              "original_amount", "current_balance", "interest_rate", "risk_grade",
              "credit_score", "property_value", "ltv_ratio", "approval_officer"]

    officers = ["A. Sharma", "B. Chen", "C. Williams", "D. Patel", "E. Martin",
                "F. Kim", "G. Brown", "H. Singh", "I. Lopez", "J. Taylor"]

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for loan in loans:
            row = {k: loan[k] for k in fields if k in loan}
            row["approval_officer"] = random.choice(officers)

            # Some name formatting inconsistencies (common in real systems)
            if random.random() < 0.05:
                row["customer_name"] = row["customer_name"].upper()
            if random.random() < 0.03:
                row["customer_name"] = row["customer_name"].lower()

            # Occasional date format inconsistency
            if random.random() < 0.02:
                d = datetime.strptime(row["origination_date"], "%Y-%m-%d")
                row["origination_date"] = d.strftime("%m/%d/%Y")

            writer.writerow(row)

    # Add ~1% orphan records (exist in LOS but not CBS — approved but not booked)
    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        for i in range(NUM_LOANS + 51, NUM_LOANS + 101):
            product = random.choice(PRODUCTS)
            writer.writerow({
                "loan_id": generate_loan_id(i),
                "customer_id": generate_customer_id(random.randint(1, 4000)),
                "customer_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "product_code": product["code"],
                "product_name": product["name"],
                "province": random.choice(PROVINCES),
                "branch_id": random.choice(BRANCHES),
                "origination_date": random_date(2024, 2025).strftime("%Y-%m-%d"),
                "maturity_date": random_date(2030, 2035).strftime("%Y-%m-%d"),
                "original_amount": round(random.uniform(product["min_amount"], product["max_amount"]), 2),
                "current_balance": round(random.uniform(5000, 200000), 2),
                "interest_rate": round(random.uniform(product["min_rate"], product["max_rate"]), 4),
                "risk_grade": random.choice(RISK_GRADES),
                "credit_score": random.randint(550, 850),
                "property_value": round(random.uniform(200000, 800000), 2) if product["code"].startswith("MTG") else 0,
                "ltv_ratio": round(random.uniform(50, 95), 2) if product["code"].startswith("MTG") else 0,
                "approval_officer": random.choice(officers),
            })

    print(f"  LOS extract: {filepath}")


def write_credit_bureau(loans):
    """Credit bureau data — external credit information."""
    filepath = OUTPUT_DIR / "credit_bureau.csv"
    fields = ["customer_id", "bureau_score", "total_debt", "num_credit_accounts",
              "num_delinquencies_12m", "bankruptcy_flag", "inquiry_count_6m",
              "oldest_account_years", "utilization_pct", "report_date"]

    seen_customers = set()
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for loan in loans:
            cid = loan["customer_id"]
            if cid in seen_customers:
                continue
            seen_customers.add(cid)

            # ~4% of customers won't have bureau data (new to credit)
            if random.random() < 0.04:
                continue

            base_score = loan["credit_score"]
            # Bureau score may differ slightly from internal score
            bureau_score = base_score + random.randint(-40, 40)
            bureau_score = max(300, min(900, bureau_score))

            writer.writerow({
                "customer_id": cid,
                "bureau_score": bureau_score,
                "total_debt": round(random.uniform(5000, 500000), 2),
                "num_credit_accounts": random.randint(1, 15),
                "num_delinquencies_12m": random.choices([0, 1, 2, 3, 4, 5],
                                                         weights=[0.60, 0.15, 0.10, 0.08, 0.05, 0.02])[0],
                "bankruptcy_flag": random.choices(["N", "Y"], weights=[0.97, 0.03])[0],
                "inquiry_count_6m": random.randint(0, 8),
                "oldest_account_years": random.randint(1, 25),
                "utilization_pct": round(random.uniform(5, 95), 1),
                "report_date": "2025-08-31",
            })

    print(f"  Credit Bureau: {filepath}")


def write_branch_metadata():
    """Branch reference data."""
    filepath = OUTPUT_DIR / "branch_metadata.csv"
    branch_data = [
        ("BR-001", "Head Office Toronto", "Toronto", "ON", "Central"),
        ("BR-002", "Midtown Toronto", "Toronto", "ON", "Central"),
        ("BR-003", "Downtown Toronto", "Toronto", "ON", "Central"),
        ("BR-004", "Scarborough", "Toronto", "ON", "Central"),
        ("BR-005", "North York", "Toronto", "ON", "Central"),
        ("BR-006", "Mississauga", "Mississauga", "ON", "Central"),
        ("BR-007", "Brampton", "Brampton", "ON", "Central"),
        ("BR-008", "Ottawa Centre", "Ottawa", "ON", "Eastern"),
        ("BR-009", "Hamilton", "Hamilton", "ON", "Central"),
        ("BR-010", "London ON", "London", "ON", "Western ON"),
        ("BR-011", "Vancouver Downtown", "Vancouver", "BC", "Pacific"),
        ("BR-012", "Vancouver Metrotown", "Burnaby", "BC", "Pacific"),
        ("BR-013", "Surrey", "Surrey", "BC", "Pacific"),
        ("BR-014", "Victoria", "Victoria", "BC", "Pacific"),
        ("BR-015", "Calgary Downtown", "Calgary", "AB", "Prairie"),
        ("BR-016", "Calgary South", "Calgary", "AB", "Prairie"),
        ("BR-017", "Edmonton", "Edmonton", "AB", "Prairie"),
        ("BR-018", "Montreal Centre", "Montreal", "QC", "Quebec"),
        ("BR-019", "Montreal East", "Montreal", "QC", "Quebec"),
        ("BR-020", "Quebec City", "Quebec City", "QC", "Quebec"),
        ("BR-021", "Winnipeg", "Winnipeg", "MB", "Prairie"),
        ("BR-022", "Saskatoon", "Saskatoon", "SK", "Prairie"),
        ("BR-023", "Halifax", "Halifax", "NS", "Atlantic"),
        ("BR-024", "Fredericton", "Fredericton", "NB", "Atlantic"),
        ("BR-025", "Kitchener", "Kitchener", "ON", "Western ON"),
    ]

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["branch_id", "branch_name", "city", "province", "region"])
        writer.writeheader()
        for b in branch_data:
            writer.writerow(dict(zip(["branch_id", "branch_name", "city", "province", "region"], b)))

    print(f"  Branch metadata: {filepath}")


def write_product_config():
    """Product configuration reference data."""
    filepath = OUTPUT_DIR / "product_config.csv"
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["product_code", "product_name", "min_amount",
                                                "max_amount", "min_rate", "max_rate", "term_months",
                                                "secured_flag", "risk_weight_pct"])
        writer.writeheader()
        risk_weights = {"MTG-FIX": 35, "MTG-VAR": 35, "HELOC": 35, "AUTO": 75,
                        "PL-SEC": 75, "PL-UNSEC": 100, "LOC": 100, "STUDENT": 75}
        for p in PRODUCTS:
            row = {
                "product_code": p["code"],
                "product_name": p["name"],
                "min_amount": p["min_amount"],
                "max_amount": p["max_amount"],
                "min_rate": p["min_rate"],
                "max_rate": p["max_rate"],
                "term_months": p["term_months"],
                "secured_flag": "Y" if p["code"] in ["MTG-FIX", "MTG-VAR", "HELOC", "AUTO", "PL-SEC"] else "N",
                "risk_weight_pct": risk_weights[p["code"]],
            }
            writer.writerow(row)

    print(f"  Product config: {filepath}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Generating synthetic loan portfolio data...")
    print(f"  Target: {NUM_LOANS} base loans\n")

    loans = generate_base_loans()
    print("Writing source system extracts:")
    write_cbs_extract(loans)
    write_los_extract(loans)
    write_credit_bureau(loans)
    write_branch_metadata()
    write_product_config()

    print(f"\nDone! Files written to: {OUTPUT_DIR}")
    print(f"  Total base loans: {NUM_LOANS}")
    print(f"  CBS orphans added: 50")
    print(f"  LOS orphans added: 50")
    print(f"  Seeded balance discrepancies: ~{int(NUM_LOANS * 0.03)}")
    print(f"  Seeded rate discrepancies: ~{int(NUM_LOANS * 0.015)}")


if __name__ == "__main__":
    main()
