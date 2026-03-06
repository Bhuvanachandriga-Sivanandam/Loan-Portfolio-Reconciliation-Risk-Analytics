# Business Rules

Reconciliation thresholds, risk classification logic, and regulatory context.

---

## Reconciliation Rules

### Match Classification

| Category | Balance Threshold | Rate Threshold | Action |
|----------|-------------------|----------------|--------|
| Exact Match | $0 | 0.0000 | No action — systems aligned |
| Tolerance Match | ≤ $50 | ≤ 0.0005 (0.05%) | Log only — within acceptable variance |
| Soft Break | $50.01 – $500.00 | 0.0005 – 0.005 | Auto-route to operations for investigation |
| Hard Break | > $500.00 | > 0.005 (0.5%) | Escalate — requires manual resolution |
| CBS Orphan | Exists in CBS only | — | Investigate: booked but not in origination system |
| LOS Orphan | Exists in LOS only | — | Investigate: approved but not yet booked |

### Escalation Matrix

| Break Value | SLA | Escalation Level |
|-------------|-----|-----------------|
| < $1,000 | 5 business days | Branch Operations |
| $1,000 – $10,000 | 3 business days | Regional Operations Manager |
| $10,000 – $100,000 | 1 business day | VP Operations |
| > $100,000 | Same day | Chief Risk Officer |

---

## Data Quality Rules

| Rule ID | Field | Condition | Severity | Rationale |
|---------|-------|-----------|----------|-----------|
| DQ-01 | loan_id | NOT NULL, NOT EMPTY | Critical | Primary key — cannot reconcile without it |
| DQ-02 | customer_id | NOT NULL, NOT EMPTY | Critical | Required for bureau matching |
| DQ-03 | current_balance | >= 0 | Critical | Negative balances indicate system error |
| DQ-04 | interest_rate | BETWEEN 0 AND 30 | High | Rates outside range suggest data corruption |
| DQ-05 | origination_date | Valid date AND <= TODAY | High | Future dates are invalid |
| DQ-06 | product_code | IN valid product list | Medium | Unmapped products cannot be risk-weighted |
| DQ-07 | branch_id | IN branch_metadata | Medium | Orphan branches affect geographic reporting |
| DQ-08 | credit_score | BETWEEN 300 AND 900 | Medium | Standard score range in Canada |
| DQ-09 | province | IN valid provinces | Low | Required for geographic analytics |
| DQ-10 | ltv_ratio | BETWEEN 0 AND 200 (if secured) | High | LTV > 200% signals valuation or data issue |
| DQ-11 | days_past_due | >= 0 | Medium | Negative DPD is logically impossible |
| DQ-12 | monthly_payment | >= 0 | Medium | Negative payments indicate reversal errors |

---

## Risk Concentration Thresholds

### HHI (Herfindahl-Hirschman Index)

| HHI Value | Interpretation |
|-----------|---------------|
| < 0.15 | Low concentration — well diversified |
| 0.15 – 0.25 | Moderate concentration — monitor |
| > 0.25 | High concentration — requires management action |

### Single-Name Exposure Limits

| Exposure Band | Policy Limit |
|---------------|-------------|
| Individual borrower | ≤ 10% of Tier 1 capital |
| Connected parties | ≤ 25% of Tier 1 capital |
| Industry sector | ≤ 20% of total portfolio |
| Geographic (province) | ≤ 40% of total portfolio |

### LTV Policy Limits

| Product | Maximum LTV | CMHC Insurance Required |
|---------|-------------|------------------------|
| Conventional Mortgage | 80% | No |
| Insured Mortgage | 95% | Yes (> 80% LTV) |
| HELOC | 65% | No |
| Combined (Mortgage + HELOC) | 80% | — |

---

## Regulatory Context

### OSFI (Office of the Superintendent of Financial Institutions)

- **Guideline B-20:** Residential mortgage underwriting — stress test at qualifying rate
- **Guideline B-6:** Liquidity adequacy — reporting standards
- **Basel III/IV:** Risk-weighted asset calculations using standardized or IRB approach

### IFRS 9 — Expected Credit Loss Staging

| Stage | Criteria | Provisioning |
|-------|----------|-------------|
| Stage 1 | Performing (no significant increase in credit risk) | 12-month ECL |
| Stage 2 | Significant increase in credit risk since origination | Lifetime ECL |
| Stage 3 | Credit-impaired (default or 90+ DPD) | Lifetime ECL (net of recovery) |

**Stage transition triggers used in this project:**
- Stage 1 → 2: DPD > 30, OR credit score drop > 50 points, OR risk grade downgrade ≥ 2 notches
- Stage 2 → 3: DPD > 90, OR status = "Default"
- Stage 3 → 2: DPD returns to < 30 AND two consecutive on-time payments (cure period)

---

## Assumptions and Limitations

1. All data is synthetic — patterns are realistic but do not represent any actual institution
2. Balance discrepancies are randomly seeded; in production, root causes would be specific (e.g., batch timing, failed postings)
3. Credit bureau data uses a simplified single-bureau model; Canadian banks typically pull from Equifax and TransUnion
4. Risk weights use Basel III Standardized Approach (simplified)
5. IFRS 9 staging logic is directional — production implementations incorporate PD/LGD models
