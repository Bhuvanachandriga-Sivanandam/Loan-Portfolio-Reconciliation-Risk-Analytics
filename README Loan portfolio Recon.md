# Loan Portfolio Reconciliation & Risk Analytics

An end-to-end data analytics solution built on **Alteryx Designer Cloud** that automates loan portfolio reconciliation across multiple banking systems and generates risk insights for proactive portfolio management.

## Business Context

Banks maintain loan data across multiple systems — Loan Origination Systems (LOS), Core Banking Systems (CBS), and Credit Bureaus — that must stay synchronized. Manual reconciliation is time-consuming, error-prone, and delays risk identification. This project automates the entire reconciliation and risk analysis pipeline using Alteryx visual workflows.

## Project Overview

| Component | Description |
|-----------|-------------|
| **Workflow 01** | Data Preparation, Reconciliation & Validation |
| **Workflow 02** | Risk Analytics & Portfolio Segmentation |
| **Data Sources** | Loan Origination System (LOS), Core Banking System (CBS), Credit Bureau |
| **Platform** | Alteryx Designer Cloud (Analytics Cloud) |
| **Use Case** | Banking Operations — Loan Portfolio Management |

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Credit Bureau   │    │   Loan LOS      │    │   Loans CBS     │
│  (credit_bureau  │    │   (loans_los    │    │   (loans_cbs    │
│   .csv)          │    │    .csv)         │    │    .csv)         │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
    Data Cleansing          Data Cleansing          Data Cleansing
    + Select                + Select                + Select
         │                       │                       │
         │                       └───────┬───────────────┘
         │                               │
         │                           Join (LOS + CBS)
         │                           on loan_id
         │                               │
         │                        Data Cleansing
         │                               │
         │                     Filter: Active Loans
         │                               │
         │                     Filter: Mismatch Flags
         │                     (Balance, Rate, Date,
         │                      Product, Customer,
         │                      Branch mismatches)
         │                               │
         │                        Formula Tool
         │                     (Balance_Mismatch,
         │                      Rate_Mismatch,
         │                      Risk_Flag)
         │                               │
         └───────────┬───────────────────┘
                     │
              Join (+ Credit Bureau)
              on customer_id
                     │
              ┌──────┴──────┐
              │             │
         Output #1     Output #2
     Reconciliation   Clean Matched
       Breaks          Records
              │
              ▼
     ┌─────────────────────────────────┐
     │     WORKFLOW 02: RISK ANALYTICS │
     ├─────────────────────────────────┤
     │                                 │
     │  ┌───────────┐ ┌────────────┐  │
     │  │ Risk by   │ │  Credit    │  │
     │  │ Province  │ │  Score     │  │
     │  │ Summary   │ │  Segments  │  │
     │  └───────────┘ └────────────┘  │
     │                                 │
     │  ┌───────────┐ ┌────────────┐  │
     │  │  Aging    │ │  Expected  │  │
     │  │  Analysis │ │  Loss      │  │
     │  │           │ │  Summary   │  │
     │  └───────────┘ └────────────┘  │
     └─────────────────────────────────┘
```

## Workflow 01: Data Preparation, Reconciliation & Validation

This workflow ingests data from three banking sources, standardizes and cleanses the data, joins the datasets, and identifies reconciliation breaks and data quality issues.

### Data Sources

**Loan Origination System (LOS)** — Contains origination-stage loan details: loan ID, customer ID, product code, branch, origination date, current balance, interest rate, status, days past due, payment dates, and monthly payment amount.

**Core Banking System (CBS)** — Contains the bank's system of record for loans: customer name, product name, province, maturity date, original amount, current balance, interest rate, risk grade, credit score, property value, LTV ratio, and approval officer.

**Credit Bureau** — External credit data used to validate borrower risk profiles and enrich portfolio analytics.

### Processing Steps

**Data Ingestion & Cleansing** — Each source is loaded, cleansed (null handling, whitespace trimming, data type standardization), and filtered to select relevant columns using Select tools.

**System Reconciliation** — LOS and CBS are joined on `loan_id` to create a unified loan record. This enables cross-system comparison to identify discrepancies.

**Active Loan Filtering** — Only active loans are passed through for reconciliation, ensuring the analysis focuses on the current portfolio.

**Mismatch Detection** — A custom filter flags records where key fields disagree between LOS and CBS:

- `current_balance` mismatch (LOS vs CBS)
- `interest_rate` mismatch
- `origination_date` mismatch
- `product_code` mismatch
- `customer_id` mismatch
- `branch_id` mismatch

**Risk Metrics Calculation** — Formula tools compute derived fields:

- **Balance_Mismatch** — Dollar difference between LOS and CBS balances
- **Rate_Mismatch** — Interest rate difference between systems
- **Risk_Flag** — Categorization based on days past due (High: >90 days, Medium: 31–90 days, Low: ≤30 days)

**Credit Bureau Enrichment** — The reconciled dataset is joined with Credit Bureau data on `customer_id` to add credit scores and external risk indicators.

### Outputs

- **Reconciliation_Breaks.csv** — Records with mismatches between LOS and CBS for investigation
- **Clean_Matched_Records.csv** — Validated records where all systems agree

## Workflow 02: Risk Analytics & Portfolio Segmentation

This workflow takes the reconciled output from Workflow 01 and produces portfolio-level risk analytics.

### Analysis Dimensions

**Risk Distribution by Province** — Summarizes loan count and total exposure by province and risk flag, identifying geographic concentrations of risk.

**Credit Score Segmentation** — Categorizes borrowers into segments based on credit scores:

| Segment | Credit Score Range |
|---------|-------------------|
| Excellent | ≥ 750 |
| Good | 650 – 749 |
| Fair | 550 – 649 |
| Poor | < 550 |

**Aging Analysis** — Groups loans by risk flag and calculates average days past due, total exposure, and loan count per category.

**Expected Loss Summary** — Applies the standard credit risk formula:

```
Expected Loss = Probability of Default (PD) × Loss Given Default (LGD) × Exposure at Default (EAD)
```

### Outputs

- **Risk_By_Province.csv** — Geographic risk distribution
- **Credit_Segmentation.csv** — Portfolio segmentation by credit quality
- **Aging_Analysis.csv** — Delinquency aging report

## Key Risk Metrics Explained

| Metric | Formula | Significance |
|--------|---------|-------------|
| LTV Ratio | Loan Amount / Property Value | Measures collateral coverage; <80% is low risk in Canada |
| Days Past Due | Current Date - Last Payment Date | Primary delinquency indicator |
| Balance Mismatch | LOS Balance - CBS Balance | Flags potential booking or posting errors |
| Rate Mismatch | LOS Rate - CBS Rate | Identifies interest rate discrepancies |
| Expected Loss | PD × LGD × EAD | Estimated dollar loss from defaults |

## Technology Stack

- **Alteryx Designer Cloud** — Visual workflow design, data blending, and transformation
- **CSV** — Data source and output format
- **GitHub** — Version control and portfolio documentation

## Skills Demonstrated

- Multi-source data integration and reconciliation
- Data quality validation and exception handling
- Risk analytics and portfolio segmentation
- Visual workflow design (ETL without code)
- Banking domain knowledge (credit risk, LTV, delinquency analysis)

## About

Built by **Bhuvanachandriga Sivanandam** — Senior Data Analyst with 7+ years of experience in banking operations, reconciliation, and automation. This project demonstrates the same reconciliation and risk analytics logic previously implemented in Python/SQL at scale (10,000+ records, uncoverig discrepancy), now replicated in Alteryx to showcase platform versatility.

[LinkedIn](https://www.linkedin.com/in/bhuvanachandriga) | [GitHub](https://github.com/Bhuvanachandriga-Sivanandam)
