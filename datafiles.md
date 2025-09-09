# 📂 Data Files — The Protector (Fire & Safety Lens)

**File:** `datafiles.md`  
**Purpose:** Explain each demo seed file and how it maps to typical Fire & Safety data sources.

---

## 1. `data/incidents.csv`
- **What it is:** A rolling log of fire alarms, intrusions, system faults, etc. Each row = 1 incident.
- **Columns:** `ts` (timestamp), `site`, `type`, `severity`, `response_min`, `resolved`.
- **Real-world source:**  
  - Alarm monitoring software or incident management system.  
  - Security access logs or fire panel logs.  
  - Often exportable as CSV/Excel for compliance reports.  

---

## 2. `data/drills.csv`
- **What it is:** Schedule + completion of required drills (fire, security, evacuation). Each row = 1 drill event at a site/month.
- **Columns:** `site`, `month`, `scheduled`, `completed`.
- **Real-world source:**  
  - Training/compliance calendar.  
  - CMMS (Computerized Maintenance Management System) tracking monthly drills.  
  - Spreadsheet owned by facilities or safety manager.  

---

## 3. `data/maintenance.csv`
- **What it is:** Equipment checks and whether they were completed on time.
- **Columns:** `site`, `asset`, `check_due`, `completed_on`.
- **Real-world source:**  
  - Preventive maintenance module of a CMMS (e.g., for sprinklers, alarm panels, cameras).  
  - Work order system (open vs closed tickets).  
  - Manual inspection logs.  

---

## 4. `data/sites.csv`
- **What it is:** Baseline info about each site for risk modeling.
- **Columns:** `site`, `ft_print` (facility size), `has_guard` (1/0), `perimeter_quality` (0–1 scale).
- **Real-world source:**  
  - Facilities database or site registry.  
  - Security provider assessments.  
  - Insurance or audit risk scoring models.  

---

## Why this matters
Together these files fuel the Fire & Safety lens of **The Protector**. In practice, **most of this data already exists** in Silco’s systems:  
- Incident data from alarm/monitoring feeds.  
- Drill data from compliance scheduling.  
- Maintenance data from CMMS or work orders.  
- Site data from facilities/security audits.  

The demo simply shows how quickly these sources can be shaped into actionable KPIs.

---
