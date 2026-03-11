# 🏦 Loan Portfolio Reconciliation & Risk Analytics

> End-to-end data analytics pipeline built in **Alteryx Designer** for detecting reconciliation discrepancies, assessing credit risk concentrations, and automating regulatory reporting across a simulated retail banking loan portfolio.

![Alteryx](https://img.shields.io/badge/Built%20With-Alteryx%20Designer-0078C1?style=flat-square)
![Python](https://img.shields.io/badge/Validation-Python%203.11-3776AB?style=flat-square)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen?style=flat-square)

---

## Business Context

In retail banking, loan data flows through multiple systems — origination platforms, core banking ledgers, credit bureaus, and collections systems. **Reconciliation failures between these systems** can lead to:

- Misstated financials and audit findings
- Incorrect provisioning (IFRS 9 / CECL exposure)
- Regulatory penalties from inaccurate Basel III/IV risk-weighted asset calculations
- Customer complaints from misapplied payments

This project simulates a **realistic multi-source reconciliation** scenario inspired by operational risk challenges in banking, and demonstrates how Alteryx can automate detection, classification, and reporting of discrepancies at scale.

---

## Project Architecture

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Core Banking     │    │  Loan Origination │    │  Credit Bureau    │
│  Ledger (CBS)     │    │  System (LOS)     │    │  Data             │
│  loans_cbs.csv    │    │  loans_los.csv    │    │  credit_bureau.csv│
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         └───────────┬───────────┘───────────────────────┘
                     ▼
        ┌────────────────────────┐
        │  WORKFLOW 1: DATA PREP │
        │  & QUALITY CHECKS      │
        │  (01_data_preparation)
                  MULTI-WAY 
        │  RECONCILIATION        │
        │  (02_reconciliation) │
        └────────────┬───────────┘
                     ▼
        ┌────────────────────────┐
        │  WORKFLOW 3: RISK      │
        │  CONCENTRATION &       │
        │  PORTFOLIO ANALYTICS   │
        │  (02_risk_analytics)   │
        └────────────┬───────────
```

---

## Workflows

### Workflow 1 — Data Preparation & Quality Checks
**File:** `workflows/01_data_preparation.yxmd`

| Alteryx Tools Used | Purpose |
|---|---|
| Input Data | Load 3 CSV source files |
| Data Cleansing | Standardize nulls, trim whitespace, fix casing |
| Auto Field | Optimize field types and sizes |
| Formula | Derive `days_past_due`, `loan_age_months`, `ltv_ratio` |
| Filter | Flag records with missing mandatory fields |
| Select | Rename and reorder columns for consistency |
| Union | Combine quality exception records |
| Output Data | Write cleaned files + exception log |

**Key Transformations:**
- Parse and standardize date formats across systems
- Calculate derived risk fields (LTV, DTI ratios, days past due)
- Flag and quarantine records failing 12 data quality rules
- Produce `data_quality_exceptions.csv` with failure reasons

---

### Workflow 2 — Multi-Way Reconciliation
**File:** `workflows/02_reconciliation.yxmd`

| Alteryx Tools Used | Purpose |
|---|---|
| Join | CBS ↔ LOS matching on loan_id |
| Join | Matched set ↔ Credit Bureau on customer_id |
| Formula | Calculate balance variance, rate variance |
| Filter | Classify: Match / Tolerance Break / Hard Break |
| Summarize | Aggregate discrepancies by type, branch, product |
| Append Fields | Enrich with branch and product metadata |
| Output Data | Reconciliation results + break details |

**Reconciliation Logic:**
- **Exact Match:** Balance difference = $0, rate difference = 0
- **Tolerance Match:** Balance difference ≤ $50 AND rate difference ≤ 0.05%
- **Soft Break:** Balance difference $50–$500 (auto-investigate)
- **Hard Break:** Balance difference > $500 OR loan exists in one system only

---

### Workflow 3 — Risk Concentration Analytics
**File:** `workflows/03_risk_analytics.yxmd`

| Alteryx Tools Used | Purpose |
|---|---|
| Summarize | Portfolio aggregation by segment |
| Cross Tab | Product × Risk Grade matrix |
| Running Total | Cumulative exposure calculations |
| Formula | HHI concentration index, weighted avg metrics |
| Sample | Top-N exposure identification |
| Multi-Row Formula | Month-over-month migration analysis |
| Output Data | Risk summary tables for dashboarding |

**Analytics Produced:**
- Portfolio distribution by product type, province, risk grade
- Herfindahl-Hirschman Index (HHI) for sector concentration
- Top 20 single-name exposures
- Risk grade migration matrix (performing → watch-list → impaired)
- Vintage analysis by origination quarter

---

### Workflow 4 — Automated Reporting
**File:** `workflows/04_reporting.yxmd`

| Alteryx Tools Used | Purpose |
|---|---|
| Table | Format reconciliation break summary |
| Charting | Discrepancy trend visualization |
| Layout | Combine tables and charts |
| Report Header/Footer | Add timestamps, run metadata |
| Render | Export as PDF and Excel |
| Email | (configured for scheduled distribution) |

---

## Dataset Description

All data is **synthetically generated** — no real customer data is used.

| File | Records | Description |
|---|---|---|
| `loans_cbs.csv` | 5,000 | Core Banking System extract — balances, rates, status |
| `loans_los.csv` | 5,000 | Loan Origination System extract — application data, approvals |
| `credit_bureau.csv` | 4,800 | Credit bureau data — scores, external obligations |
| `branch_metadata.csv` | 25 | Branch reference data — region, province |
| `product_config.csv` | 8 | Product type configuration — terms, rate bands |

**Intentionally seeded discrepancies:**
- ~3% balance mismatches (simulating posting errors)
- ~1.5% rate discrepancies (system sync lag)
- ~2% orphaned records (exist in one system only)
- ~0.5% duplicate loan IDs

---

## Repository Structure

```
alteryx-loan-reconciliation/
├── README.md
├── data/
│   ├── raw/                        # Source system extracts
│   │   ├── loans_cbs.csv
│   │   ├── loans_los.csv
│   │   ├── credit_bureau.csv
│   │   ├── branch_metadata.csv
│   │   └── product_config.csv
│   └── processed/                  # Workflow outputs
│       ├── cleaned_loans.csv
│       ├── data_quality_exceptions.csv
│       ├── reconciliation_results.csv
│       ├── hard_breaks.csv
│       ├── risk_concentration.csv
│       └── portfolio_summary.csv
├── workflows/                      # Alteryx Designer files
│   ├── 01_data_preparation.yxmd
│   ├── 02_reconciliation.yxmd
│   ├── 03_risk_analytics.yxmd
│   └── 04_reporting.yxmd
├── scripts/                        # Python validation scripts
│   ├── generate_sample_data.py     # Reproducible data generation
│   └── validate_outputs.py         # Cross-check Alteryx results
├── output/                         # Final reports
│   └── reconciliation_report.pdf
├── docs/
│   ├── workflow_guide.md           # Step-by-step build instructions
│   ├── data_dictionary.md          # Field-level documentation
│   └── business_rules.md           # Reconciliation & risk rules
└── .gitignore
```

---

## How to Reproduce

### Prerequisites
- Alteryx Designer (Community Edition / 30-day trial)
- Python 3.9+ (for data generation and validation only)

### Steps
1. Clone this repository
2. Run `python scripts/generate_sample_data.py` to create fresh sample data
3. Open each workflow in Alteryx Designer in sequence (01 → 04)
4. Update Input Data tool paths to point to your local `data/raw/` directory
5. Run each workflow — outputs land in `data/processed/`

---

## Key Findings (from sample run)

| Metric | Value |
|---|---|
| Total loans reconciled | 5,000 |
| Exact matches | 4,412 (88.2%) |
| Tolerance matches | 198 (4.0%) |
| Soft breaks | 241 (4.8%) |
| **Hard breaks** | **149 (3.0%)** |
| Total discrepancy value | **$2.87M** |
| Largest single break | $47,200 |
| Most impacted product | Unsecured Personal Loans |
| Most impacted branch | Downtown Toronto (Branch 003) |

---

## Skills Demonstrated

| Skill | Application |
|---|---|
| **Data Blending** | Multi-source join across CBS, LOS, and Credit Bureau |
| **Data Quality** | 12-rule validation framework with exception logging |
| **Reconciliation** | Configurable tolerance-based matching engine |
| **Risk Analytics** | HHI concentration, vintage analysis, migration matrices |
| **Reporting** | Automated PDF/Excel with charts and formatted tables |
| **Automation** | Designed for Alteryx Server scheduled execution |
| **Documentation** | Full data dictionary, business rules, build guide |

---

## About

Built by **Bhuvanachandriga** — Senior Data Analyst with 7+ years in banking & financial services. This project demonstrates applied analytics capabilities in loan portfolio management, operational risk, and regulatory reporting.

[LinkedIn](#) · [Portfolio](#)

---

## License

This project uses synthetic data only. No real customer or financial institution data is included. MIT License.
