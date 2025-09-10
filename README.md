# 🛡️ The Protector  
**Core System :: Guardian**

The Protector safeguards the constellation by promoting **integrity** — hardening workflows, monitoring health, and shortening recovery time.  
For this opportunity, it is presented through a **Fire & Safety lens** to demonstrate how incidents, readiness, and response can be tracked and improved.

---

## Fire & Safety Lens (Demo)

This temporary view highlights KPIs relevant to the Fire & Security vertical:

- **Incidents (30d):** Severity-weighted count of events.  
- **High-Severity %:** Share of incidents that are critical or major.  
- **Median Response Time:** Minutes to resolve alarms or alerts.  
- **Drill Compliance:** % of scheduled drills completed on time.  
- **Asset Protection Score:** Composite 0–100 rating based on equipment health + compliance.  
- **Preventive Health:** Count of overdue maintenance checks.  
- **False Alarm Rate:** % of triggered events that were false positives.  
- **MTTR:** Mean time to recovery following an incident.  

Supporting context:  
- **Incident Mix** shows the breakdown of fire, intrusion, and system faults.  
- **Top Sites by Risk** highlights facilities needing attention.

## Schema
- sites: site_id, site_name, site_type, occupancy_class, has_sprinklers, sq_ft, city, address, ahj_jurisdiction, installed_year, system_age_years, service_level, risk_score
- drills: drill_id, site_id, scheduled_date, completed, passed, evac_time_seconds
- maintenance: maintenance_id, site_id, scheduled_date, completed, technician, task_type, parts_cost
- incidents: incident_id, site_id, incident_date, incident_type (False Alarm/Real Event), severity_1to5, property_loss_usd

---

## Core System Role (Permanent)

Beyond the Fire & Safety demo, The Protector is seeded as a **Core System** within the constellation.  
Its long-term mission is to safeguard the constellation’s **integrity**:

- **Uptime monitoring** across Pages and workflows.  
- **Failed pulses tracking** (Archive, Signal, etc.).  
- **Secrets hygiene** (credentials rotation, leak scans).  
- **Auth anomaly detection** (suspicious pushes, workflow edits).  
- **MTTR** for systemic incidents.

This aligns with the other Core Systems:  
- 🚀 The Launch → promotes consistency  
- 🫀 The Archive → promotes longevity  
- 📡 The Signal → promotes opportunity  
- 🛡️ The Protector → promotes integrity

---

## Demo Flow

1. Click **Run Check** on the dashboard face.  
2. Watch KPIs populate with sample values.  
3. Walk through 2–3 highlights (e.g., response time vs. drill compliance).  
4. Tie the insights back to readiness and resilience.  

---

## Roadmap

- **v0.1:** Fire & Safety lens with demo KPIs (current state).  
- **v0.2:** Wire to real probes (GitHub Actions uptime, pulse logs).  
- **v0.3:** Secrets & token hygiene reports.  
- **v0.4:** Auth anomaly monitoring.  
- **v0.5:** Constellation-wide Guardian role fully in place.

---

## Status

**Active (Core Systems)**. Fire & Safety lens enabled for demonstration purposes.
