# The Protector — Quantifying the Trust Gap

## Purpose

This project demonstrates how data analytics can expose the fine line between trust and risk.  
Using a public Kaggle dataset (**Credit Card Fraud Detection**), the model explains how behavioral anomalies — spending spikes, device reuse, or timing drift — shape the probability of fraud.  
The intent isn’t to police transactions, but to clarify when and why trust breaks down.

---

## 1. Executive Overview

Fraud analytics lives in tension: too much protection slows customers down, too little invites loss.  
The goal is to measure that tension — to quantify risk lift while preserving experience.  

Through a reproducible Python model and a Power BI dashboard, the Protector Model turns raw transactions into a transparent story: how risk grows, where detection pays off, and what trade-offs define “enough” protection.

**Deliverables include:**

- `fraud.py` — Python pipeline for data cleaning, model training, scoring, and artifact export  
- `consumer_protection.pbix` — Power BI dashboard visualizing fraud probabilities and trade-offs  
- `signals/baseline_metrics.json` — live KPI snapshot for the model’s performance  
- `model.html` — lightweight UI for viewing the signal metrics  
- `executive_brief.pdf` — one-page narrative connecting model insight to operational outcomes  

---

## 2. Business Context & Data

Fraud prevention is trust management at scale.  
Each transaction is a behavioral signal — some signals just arrive distorted.  

The analysis uses the **Credit Card Fraud Detection** dataset (284,807 records, 0.17% fraud), containing anonymized numerical features (V1–V28), transaction amount, and a binary *Class* label.

**Key fields and derived metrics:**

- `Amount`, `Time`, `V1–V28`, `Class`
- Derived: transaction velocity, normalized amount, probability score (`proba`)

**Outputs:**

- `creditcard_clean.parquet` (clean data)
- `transactions_with_scores.parquet` (scored data with model probabilities)

---

## 3. Analytical Approach

**Phase 1 — Structuring the Data**  
Deduplicate, cast types, scale continuous fields, and export reproducible Parquet files.

**Phase 2 — Exploring Patterns**  
Use Power BI visuals to surface fraud density across amount, time of day, and velocity outliers.

**Phase 3 — Modeling for Insight**  
Train a balanced logistic regression baseline to estimate fraud probability.  
Tune and interpret precision/recall trade-offs through threshold adjustment.

**Phase 4 — Signaling and Monitoring**  
Export live KPIs to JSON (`signals/baseline_metrics.json`) and visualize them through `model.html`.  
Each model run updates the signal file, giving a lightweight “heartbeat” for ongoing monitoring.

---

## 4. Dashboard & Visualization

The `consumer_protection.pbix` dashboard reframes fraud modeling as a trust story:

- **Overview** – KPIs on fraud rate, recall, and precision  
- **Risk Simulation** – What-if slider for threshold tuning  
- **Behavioral Patterns** – Amount and time distributions segmented by fraud probability  
- **Trust Balance** – Visualization of false positives vs. fraud caught  

Each page walks stakeholders from detection to decision: when the model raises the flag, what does that cost or save?

---

## 5. Expected Outcomes

Fraud remains rare but concentrated: <1% of transactions, often clustered by velocity or amount.  
The baseline model captures ~87% of known fraud cases with ~6% precision (default 0.5 threshold).  
Raising the detection threshold can reach ~90% precision at the cost of recall — a visual, adjustable trade-off in Power BI.  

**The takeaway:** protective action is tunable, not binary.

---

## 6. Reflective Narrative — From Code to Clarity

Analytics is translation work — from confusion to coherence.  
This model doesn’t just classify; it narrates how trust erodes, step by step.

**The workflow:**
> Structure → Model → Signal → Story

Each stage yields transparency: a pipeline you can rerun, a dashboard you can explore, and a one-page brief you can read without touching the code.

---

## 7. Artifacts

| Type | Artifact | Description |
|------|-----------|-------------|
| Pipeline | `fraud.py` | Complete Python workflow for data prep, modeling, and export |
| Dashboard | `consumer_protection.pbix` | Interactive Power BI dashboard for fraud probability and threshold tuning |
| Signals | `signals/baseline_metrics.json` | Model KPI snapshot (precision, recall, F1, timestamp) |
| UI | `model.html / model.css / model.js` | Front-end viewer for KPI JSON |
| Outputs | `creditcard_clean.parquet / transactions_with_scores.parquet` | Clean and scored data files |
| Brief | `executive_brief.pdf` | Non-technical narrative linking model results to business risk decisions |

---

## 8. Reproducibility & Ethics

- Based on open, anonymized Kaggle data (no PII).  
- Deterministic seeds for consistent scoring.  
- Transparent artifacts: every output versioned and inspectable.  
- **Educational use only** — designed to illustrate risk communication, not operational fraud screening.
