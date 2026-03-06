# Workflow Build Guide

Step-by-step instructions for building each Alteryx workflow from scratch. Follow workflows 01 through 04 in sequence — each workflow's output feeds the next.

---

## Prerequisites

- Alteryx Designer (Community Edition or Trial)
- Sample data generated via `python scripts/generate_sample_data.py`
- All CSV files in `data/raw/`

---

## Workflow 01 — Data Preparation & Quality Checks

**Goal:** Clean and standardize data from three source systems. Flag quality exceptions.

### Step 1: Input the Source Files

1. Drag three **Input Data** tools onto the canvas
2. Point them to: `loans_cbs.csv`, `loans_los.csv`, `credit_bureau.csv`
3. Verify field types in the Configuration panel (especially dates and numerics)

### Step 2: Standardize CBS Data

1. Add a **Data Cleansing** tool after the CBS input
   - Check: Remove leading/trailing whitespace
   - Check: Remove null rows
2. Add a **Select** tool to rename fields for consistency:
   - `current_balance` → `cbs_balance`
   - `interest_rate` → `cbs_rate`
   - `status` → `cbs_status`
3. Add a **DateTime** tool to parse `origination_date` to proper date format
4. Add a **Formula** tool to calculate:
   - `loan_age_months`: `DateTimeDiff([origination_date], DateTimeNow(), "months")`

### Step 3: Standardize LOS Data

1. Add a **Data Cleansing** tool after the LOS input
2. Add a **Formula** tool to fix inconsistent name casing:
   - `customer_name_clean`: `TitleCase([customer_name])`
3. Add a **RegEx** tool to standardize date formats:
   - Parse `origination_date` — handle both `YYYY-MM-DD` and `MM/DD/YYYY`
4. Add a **Select** tool to rename:
   - `current_balance` → `los_balance`
   - `interest_rate` → `los_rate`

### Step 4: Data Quality Checks

Add a **Filter** tool after each cleansed stream. Route records failing ANY rule to the False output:

| Rule # | Field | Condition | Severity |
|--------|-------|-----------|----------|
| DQ-01 | loan_id | Is not null AND not empty | Critical |
| DQ-02 | customer_id | Is not null AND not empty | Critical |
| DQ-03 | current_balance | >= 0 | Critical |
| DQ-04 | interest_rate | Between 0 and 30 | High |
| DQ-05 | origination_date | Is valid date AND <= today | High |
| DQ-06 | product_code | Is in valid product list | Medium |
| DQ-07 | branch_id | Is in branch_metadata list | Medium |
| DQ-08 | credit_score | Between 300 and 900 | Medium |
| DQ-09 | province | Is in valid province list | Low |
| DQ-10 | ltv_ratio | Between 0 and 200 (if secured) | High |
| DQ-11 | days_past_due | >= 0 | Medium |
| DQ-12 | monthly_payment | >= 0 | Medium |

**Implementation approach:**
- Use a **Formula** tool to create a `dq_flag` field with concatenated rule codes
- Use a **Filter** to split clean records (empty flag) from exceptions
- Add a **Union** to combine all exception records
- Use an **Output Data** tool to write `data_quality_exceptions.csv`

### Step 5: Output Cleaned Data

1. Add **Output Data** tools for each cleaned stream
2. Write to `data/processed/` directory:
   - `cleaned_cbs.csv`
   - `cleaned_los.csv`
   - `cleaned_bureau.csv`

---

## Workflow 02 — Multi-Way Reconciliation

**Goal:** Match loans across systems and classify discrepancies.

### Step 1: Join CBS and LOS

1. Drag two **Input Data** tools for the cleaned CBS and LOS files
2. Add a **Join** tool:
   - Join on: `loan_id`
   - Left (L): CBS records
   - Right (R): LOS records
   - Output: Joined (J), Left-only (L), Right-only (R)

### Step 2: Calculate Variances

Add a **Formula** tool to the Joined output:

```
balance_variance = Abs([cbs_balance] - [los_balance])
rate_variance = Abs([cbs_rate] - [los_rate])
balance_pct_variance = IF [los_balance] > 0 THEN [balance_variance] / [los_balance] * 100 ELSE 0 ENDIF
```

### Step 3: Classify Matches

Add a **Formula** tool for classification:

```
match_type =
  IF [balance_variance] = 0 AND [rate_variance] = 0 THEN "Exact Match"
  ELSEIF [balance_variance] <= 50 AND [rate_variance] <= 0.0005 THEN "Tolerance Match"
  ELSEIF [balance_variance] <= 500 THEN "Soft Break"
  ELSE "Hard Break"
  ENDIF
```

### Step 4: Handle Orphan Records

1. Connect the Left-only output (CBS orphans) to a **Formula** tool:
   - Add field: `match_type = "CBS Orphan - Not in LOS"`
2. Connect the Right-only output (LOS orphans) to a **Formula** tool:
   - Add field: `match_type = "LOS Orphan - Not in CBS"`

### Step 5: Combine and Enrich

1. Use a **Union** tool to merge: Joined results + CBS orphans + LOS orphans
2. Add a **Join** tool to enrich with `branch_metadata.csv` on `branch_id`
3. Add a **Join** tool to enrich with `product_config.csv` on `product_code`

### Step 6: Summarize

Add a **Summarize** tool:
- Group by: `match_type`, `product_code`, `branch_id`
- Sum: `balance_variance`
- Count: `loan_id`
- Max: `balance_variance`

### Step 7: Output

Write two files:
- `reconciliation_results.csv` — all records with match classification
- `hard_breaks.csv` — filtered to Hard Breaks and Orphans only

---

## Workflow 03 — Risk Concentration Analytics

**Goal:** Analyze portfolio risk distribution and identify concentrations.

### Step 1: Load Reconciled Data

Input the `reconciliation_results.csv` from Workflow 02. Filter to matched/tolerance records only (exclude orphans for portfolio analytics).

### Step 2: Portfolio Distribution

Add a **Summarize** tool grouped by `product_code`:
- Sum: `los_balance` (total exposure)
- Count: `loan_id` (number of loans)
- Average: `credit_score`, `ltv_ratio`, `interest_rate`

### Step 3: Cross Tab — Product × Risk Grade

1. Add a **Cross Tab** tool:
   - Group by: `product_code`
   - Column header: `risk_grade`
   - Values: Sum of `los_balance`
2. This creates a matrix showing exposure concentration

### Step 4: HHI Concentration Index

Add a **Summarize** grouped by `product_code` for total exposure, then a **Formula**:

```
market_share = [product_exposure] / [total_portfolio_exposure]
hhi_component = [market_share] * [market_share]
```

Sum all `hhi_component` values. HHI > 0.25 indicates high concentration.

### Step 5: Top Exposures

1. Add a **Sort** tool on `los_balance` descending
2. Add a **Sample** tool — first 20 records
3. This gives the Top 20 single-name exposures

### Step 6: Geographic Analysis

Add a **Summarize** grouped by `province` and `region`:
- Sum: exposure
- Count: loans
- Average: credit score, LTV

### Step 7: Output

Write to `data/processed/`:
- `risk_concentration.csv`
- `portfolio_summary.csv`
- `top_exposures.csv`

---

## Workflow 04 — Automated Reporting

**Goal:** Generate formatted exception reports.

### Step 1: Load Summary Data

Input the processed files from Workflows 02 and 03.

### Step 2: Build Report Header

1. Add a **Report Header** tool
2. Configure: Report title, run date/time, data as-of date
3. Add executive summary text

### Step 3: Format Tables

Use **Table** tools to format:
- Reconciliation summary (match types with counts and values)
- Top 10 hard breaks by value
- Portfolio concentration by product
- Geographic distribution

### Step 4: Add Visualizations

Use **Charting** tools:
- Bar chart: Discrepancies by product type
- Pie chart: Match type distribution
- Heat map: Province × Product exposure

### Step 5: Layout and Render

1. Use **Layout** tools to arrange tables and charts
2. Add **Report Footer** with disclaimer text
3. Use **Render** tool to export as:
   - PDF → `output/reconciliation_report.pdf`
   - Excel → `output/reconciliation_report.xlsx`

---

## Alteryx Tools Cheat Sheet

Here's a summary of every Alteryx tool used across all four workflows:

| Category | Tools |
|---|---|
| **Input/Output** | Input Data, Output Data |
| **Preparation** | Data Cleansing, Auto Field, Select, Formula, Filter, Sort, Sample |
| **Join** | Join, Union, Append Fields |
| **Parse** | DateTime, RegEx |
| **Transform** | Summarize, Cross Tab, Running Total, Multi-Row Formula, Transpose |
| **Reporting** | Table, Charting, Layout, Report Header, Report Footer, Render |
| **Developer** | Email (for scheduling) |

This covers the **core 20+ tools** that appear in most Alteryx certification exams and job requirements.

---

## Tips for Learning

1. **Build incrementally** — run the workflow after each new tool to verify output
2. **Use Browse tools** liberally during development to inspect intermediate results
3. **Comment your workflow** — add Comment tools explaining business logic
4. **Use containers** — group related tools in Tool Containers for organization
5. **Screenshot your workflows** — these make great GitHub documentation

---

## Estimated Build Time

| Workflow | Difficulty | Estimated Time |
|---|---|---|
| 01 — Data Preparation | Beginner | 2–3 hours |
| 02 — Reconciliation | Intermediate | 3–4 hours |
| 03 — Risk Analytics | Intermediate | 2–3 hours |
| 04 — Reporting | Beginner–Intermediate | 2–3 hours |
| **Total** | | **9–13 hours** |

This maps well to a 3–4 day focused learning sprint.
