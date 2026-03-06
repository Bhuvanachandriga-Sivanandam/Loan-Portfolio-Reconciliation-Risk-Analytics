# Data Dictionary

Field-level documentation for all source and derived datasets.

---

## Source Files

### loans_cbs.csv — Core Banking System Extract

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| loan_id | String | Unique loan identifier | LN-0000001 |
| customer_id | String | Customer identifier | CUST-003421 |
| product_code | String | Product type code | MTG-FIX |
| branch_id | String | Originating branch | BR-003 |
| origination_date | Date | Loan booking date | 2022-03-15 |
| current_balance | Decimal | Outstanding balance as of extract date | 245,320.50 |
| interest_rate | Decimal | Current annual interest rate | 5.2500 |
| status | String | Current loan status | Active |
| days_past_due | Integer | Number of days payment is overdue | 0 |
| last_payment_date | Date | Date of most recent payment | 2025-08-10 |
| next_payment_date | Date | Next scheduled payment date | 2025-09-15 |
| monthly_payment | Decimal | Monthly installment amount | 1,450.00 |

### loans_los.csv — Loan Origination System Extract

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| loan_id | String | Unique loan identifier | LN-0000001 |
| customer_id | String | Customer identifier | CUST-003421 |
| customer_name | String | Full name (may have casing issues) | James Smith |
| product_code | String | Product type code | MTG-FIX |
| product_name | String | Product display name | Fixed Rate Mortgage |
| province | String | Province code | ON |
| branch_id | String | Originating branch | BR-003 |
| origination_date | Date | Application approval date (may differ from CBS) | 2022-03-15 |
| maturity_date | Date | Loan maturity date | 2047-03-15 |
| original_amount | Decimal | Originally approved amount | 350,000.00 |
| current_balance | Decimal | LOS-tracked balance | 245,320.50 |
| interest_rate | Decimal | Approved interest rate | 5.2500 |
| risk_grade | String | Internal risk classification | A |
| credit_score | Integer | Credit score at origination | 742 |
| property_value | Decimal | Collateral value (secured loans only) | 520,000.00 |
| ltv_ratio | Decimal | Loan-to-value ratio (%) | 67.50 |
| approval_officer | String | Approving officer name | A. Sharma |

### credit_bureau.csv — External Credit Bureau Data

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| customer_id | String | Customer identifier (join key) | CUST-003421 |
| bureau_score | Integer | External credit score | 735 |
| total_debt | Decimal | Total reported debt obligations | 312,500.00 |
| num_credit_accounts | Integer | Total credit accounts on file | 6 |
| num_delinquencies_12m | Integer | Delinquencies in past 12 months | 0 |
| bankruptcy_flag | String | Bankruptcy on record (Y/N) | N |
| inquiry_count_6m | Integer | Hard inquiries in past 6 months | 2 |
| oldest_account_years | Integer | Age of oldest account | 12 |
| utilization_pct | Decimal | Credit utilization percentage | 42.5 |
| report_date | Date | Bureau report as-of date | 2025-08-31 |

### branch_metadata.csv — Reference Data

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| branch_id | String | Branch identifier | BR-003 |
| branch_name | String | Branch display name | Downtown Toronto |
| city | String | City | Toronto |
| province | String | Province code | ON |
| region | String | Regional grouping | Central |

### product_config.csv — Reference Data

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| product_code | String | Product identifier | MTG-FIX |
| product_name | String | Product display name | Fixed Rate Mortgage |
| min_amount | Decimal | Minimum loan amount | 100,000.00 |
| max_amount | Decimal | Maximum loan amount | 800,000.00 |
| min_rate | Decimal | Floor rate | 4.50 |
| max_rate | Decimal | Ceiling rate | 6.50 |
| term_months | Integer | Standard term in months | 300 |
| secured_flag | String | Collateral required (Y/N) | Y |
| risk_weight_pct | Integer | Basel regulatory risk weight (%) | 35 |

---

## Derived Fields

| Field | Source Workflow | Calculation |
|-------|---------------|-------------|
| loan_age_months | WF01 | DateDiff(origination_date, today, months) |
| dq_flag | WF01 | Concatenated data quality rule violations |
| cbs_balance / los_balance | WF02 | Renamed from source-specific balance fields |
| balance_variance | WF02 | Abs(cbs_balance - los_balance) |
| rate_variance | WF02 | Abs(cbs_rate - los_rate) |
| balance_pct_variance | WF02 | balance_variance / los_balance × 100 |
| match_type | WF02 | Classification based on variance thresholds |
| market_share | WF03 | product_exposure / total_portfolio_exposure |
| hhi_component | WF03 | market_share² |

---

## Status Values

| Status | Description | DPD Range |
|--------|-------------|-----------|
| Active | Current, performing loan | 0 days |
| Delinquent-30 | 30-day delinquency | 30–59 days |
| Delinquent-60 | 60-day delinquency | 60–89 days |
| Delinquent-90 | 90-day delinquency | 90–179 days |
| Default | Non-performing / write-off candidate | 180+ days |
| Closed | Fully repaid or settled | N/A |
| Restructured | Terms modified due to hardship | 0–30 days |

## Risk Grades

| Grade | Description | Approx. Score Range |
|-------|-------------|-------------------|
| AAA | Prime / Excellent | 790–900 |
| AA | Near-prime / Very Good | 750–810 |
| A | Good | 710–770 |
| BBB | Acceptable | 670–730 |
| BB | Watch-list | 620–680 |
| B | Substandard | 570–630 |
| CCC | Doubtful / High Risk | 520–580 |
