# 🛡️ The Protector — Fire & Safety Demo Script
**File:** `demo_script.md`  
**Use:** 30-minute conversation demo (Silco Fire & Security)

---

## 0) Pre-Flight (1 min)
- Open: `https://zbreeden.github.io/protector-model/`
- Verify **Run Check** button appears.
- Confirm CSVs exist and load (`/data/incidents.csv`, `drills.csv`, `maintenance.csv`, `sites.csv`).
- Optional: Open DevTools Console to watch for errors.

---

## 1) Opening (30–45s)
> “I built a Fire & Safety lens inside my Core System called **The Protector**. The core mission is **integrity**—making risk visible and recovery faster. For Silco, I’m showing incident readiness and response. This lens is temporary for the role; the core system persists across my portfolio.”

---

## 2) Live Click (10–15s)
- Click **Run Check**.
- Pause 1–2 seconds as the cards populate.

> “Let’s generate today’s Fire & Safety picture from seeded data.”

---

## 3) Executive Readout (2–3 min)
Focus on three cards to tell a crisp story. Use this sequence:

### (A) Response & Readiness
- **Median Response Time**: “We’re at ~6–8 minutes median. That’s strong for alarm response.”
- **Drill Compliance**: “We’re above 90% this month. That’s a good leading indicator of readiness.”

### (B) Risk & Prevention
- **Preventive Health**: “We have overdue maintenance items—these are cheap to fix and reduce incidents later.”
- **Asset Protection Score**: “Sites without guard coverage or weaker perimeter drop the score; we can raise it by tightening controls and clearing maintenance.”

### (C) Incident Profile
- **Incidents (30d) + High-Severity %**: “Total volume + severity proportion drives staffing and escalation rules.”
- **Incident Mix & Top Sites by Risk**: “Intrusions cluster at Warehouse 4; fires cluster at Plant 3—different interventions by site.”

---

## 4) Optional Deep Dives (pick 1–2 if asked)
### Drill Compliance
> “We’re computing per-month scheduled vs completed from `drills.csv`. Thresholds can be tuned to your SLA.”

### MTTR vs Response Time
> “Median response is ‘first action’; **MTTR** is full recovery. Here we’re averaging ~40m. I would segment MTTR by incident type for targeted improvements.”

### False Alarm Rate
> “We flag `system_fault`/low-severity as a proxy. With real feeds, I’d split by sensor class to reduce nuisance trips.”

---

## 5) How It Would Wire in Production (60–90s)
- **Incidents feed** → alarm/incident logs (timestamp, site, type, severity, response, resolved).
- **Readiness** → drill scheduler export or CMMS tasks.
- **Maintenance** → CMMS “due” + “overdue” queries.
- **Risk model** → guards/perimeter, sensor uptime, last inspection; roll into a 0–100 protection score.

> “Day 1: point these CSVs at your exports. Week 1: live feeds + alerts when thresholds are crossed.”

---

## 6) Questions You Can Ask (discovery)
- “Where do alarm/incident logs live today (CSV export/REST/SQL)?”
- “How do you define ‘resolved’ in your process?”
- “What’s drill SLA and who owns the schedule?”
- “Which CMMS do you use? Can we pull ‘overdue’ and ‘due soon’ by site?”
- “Do you maintain a standard risk score per facility?”

---

## 7) Closing (30–45s)
> “This Fire & Safety lens is one mode of **The Protector**. The core system ensures integrity across my portfolio—uptime, pulses, secrets, anomalies. If we proceed, I’ll connect your real feeds, tune thresholds, and hand you a living dashboard with alerting and owners.”

**Call-to-Action:** “If you send a 30–60 day incident export, I’ll load it and tailor the thresholds by Friday next.”

---

## Appendix

### A1. What The Cards Mean
- **Incidents (30d):** count of events within 30 days.
- **High-Severity %:** `high / total`.
- **Median Response Time:** median of `response_min`.
- **Drill Compliance:** `completed / scheduled` for latest month.
- **Asset Protection Score:** demo 0–100 from guards/perimeter minus overdue penalties.
- **Preventive Health:** count of overdue maintenance items.
- **False Alarm Rate:** % of low-severity system faults (proxy).
- **MTTR:** mean `response_min` of resolved events (demo proxy for recovery).

### A2. Data Files (demo seeds)
- `data/incidents.csv` → `ts,site,type,severity,response_min,resolved`
- `data/drills.csv` → `site,month,scheduled,completed`
- `data/maintenance.csv` → `site,asset,check_due,completed_on`
- `data/sites.csv` → `site,ft_print,has_guard,perimeter_quality`

### A3. Troubleshooting
- **Blank cards?** Open DevTools → Network; ensure CSVs load (200 OK).
- **No change on click?** Confirm `id="run"` exists and the button isn’t disabled.
- **Wrong numbers?** Check CSV headers exactly match the names above; ensure timestamps are within 30 days for the incident count.

---

## One-Minute Pitch (if time is tight)
> “I built a Fire & Safety view inside my Core System called The Protector. Click *Run Check*, and we see response, readiness, and risk by site. In production I’d swap these CSVs for your incident and CMMS feeds, tune thresholds to your SLA, and alert owners when response or maintenance slips. It’s tailored for Silco now, but lives as a reusable integrity layer across my portfolio.”
