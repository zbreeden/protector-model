# Pen-and-Paper Acquisition Intake — Demo Pack

This pack simulates a newly acquired site that exists only on paper. You will demo how Silco uses **Salesforce + The Protector** to normalize messy intake data, create a baseline Work Order, and surface risks in Power BI.

## Files
- `raw_pen_paper_intake.csv` — messy source rows from a scanned packet
- `mapping_config.yml` — normalization and inference rules (typos, products, frequency)
- `normalize_pen_paper.py` — ETL that emits Salesforce-shaped CSVs + a quality report
- `sample_quality_report.csv` — what the script will produce for the sample rows

## How to run locally
```bash
python normalize_pen_paper.py raw_pen_paper_intake.csv mapping_config.yml normalized_out/
```

Outputs (in `normalized_out/`):
- `sites__c.csv`, `assets.csv`, `maintenance_plans__c.csv`
- `work_orders.csv`, `inspections__c.csv`, `deficiencies__c.csv`
- `quality_report.csv` (to show stakeholders exactly what was fixed or flagged)

## Demo storyline
1) Show `raw_pen_paper_intake.csv` — highlight typos, inconsistent dates, and vague equipment notes.
2) Run the ETL to produce normalized Salesforce-shaped tables.
3) In Power BI, refresh to show:
   - **Quality panel**: count of issues by type (invalid dates, typos, abbreviations).
   - **Risk panel**: Open deficiencies for new acquisitions (A/B/C), by branch.
   - **Action panel**: New intake Work Orders created with 7-day due date.
4) Close with “Day 30” goal: all acquisitions migrated, certificates on file, backlog ≤ target.

