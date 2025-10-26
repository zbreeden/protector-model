# Protector Model

> **The Protector is the guardian - maintaining constellation integrity through health monitoring and lifecycle protection**

## 🌌 Constellation Information

- **Module Key**: `protector_model`  
- **Repository**: `protector-model`
- **Orbit**: 🪐
- **Status**: 🚧
- **Emoji**: 🛡️

## 🚀 Quick Start

1. **Review seeds/**: Adapt seeded data for this module
2. **Configure schemas/**: Update schema definitions as needed  
3. **Generate signals/**: Create latest.json broadcast file

## 📡 Broadcasting

This module produces a `signals/latest.json` file conforming to the constellation's broadcast schema. The Signal (📡) aggregates these across all stars.  Use new-broadcast.sh within /scripts to run a new broadast.

## 🔗 CORE SYSTEM Links

- **Hub**: [FourTwenty Analytics](https://github.com/zbreeden/FourTwentyAnalytics)
- **The Archive**: Glossary, tags, and canonical definitions pulled down nightly and distributed out for constellation harmony.
- **The Signal**: Cross-constellation broadcasting and telemetry pulled and circulated nightly to foster promotion and development.
- **The Launch**: Detailed workflows pulled in nightly to assure an aligned culture of process improvement that starts from the Barycenter outwards to foster healthy architecture.
- **The Protector**: Examines workflows to assure drift is minimal fostering sustainability.
- **The Develper**: Feeds the constellation data for healthy modelling.

## 🛠️ Protector generator (funnel progress)

A generator script was recently added to produce a workflow-style "funnel progress" signal from the Protector's YAML seeds. It mirrors the Coach generator behavior but is adapted to the Protector schema (skills → protectors → steps).

Location:

- Script: `protector-model/scripts/generate_funnel_progress.py`
- Seed: `protector-model/seeds/funnel_spec.yml`
- JSON output: `protector-model/signals/funnel_progress.json`
- CSV summary: `protector-model/data/internal/log.report.csv`

What it does:

- Reads the Protector YAML seed and extracts `skills` → `protectors` → `steps`.
- Computes a running total for each protector using `protector_total_count` (falls back to summing step counts or counting step entries when missing).
- Computes `percent_complete` against a control flow target (default: 150), clamped to 0–100%.
- Preserves per-step metrics (e.g., `step_metric`, `step_metric_value`) and status emojis/flags.
- Serializes dates to ISO strings and writes a tidy JSON payload and a CSV summary for inspection / automation.

Generated JSON shape (summary):

```json
{
  "generated_at": "2025-10-26T00:00:00Z",
  "trainings": {
    "protector_id": {
      "id": "protector_id",
      "title": "Protector Title",
      "steps_total": 13,
      "steps_completed": [],
      "percent_complete": 8.6667,
      "last_activity": "2025-10-26",
      "notes": "...",
      "steps": [
        {"id": "rhh_01", "title": "Resting Heart Rate Logging", "metric": 62, "metric_unit": "bpm", "count": null, "status": "🌱", "last_activity": "2025-10-14"},
        ...
      ]
    }
  },
  "orphans": []
}
```

CSV output columns (one row per protector):

- id, title, steps_total, percent_complete, last_activity, notes

Run examples (from repo root, absolute paths shown):

```bash
# Dry-run (prints discovered protectors)
python3 /Users/zachrybreeden/Desktop/FourTwentyAnalytics/protector-model/scripts/generate_funnel_progress.py --dry-run

# Write JSON + CSV (control target 150)
python3 /Users/zachrybreeden/Desktop/FourTwentyAnalytics/protector-model/scripts/generate_funnel_progress.py \
  --funnel-spec /Users/zachrybreeden/Desktop/FourTwentyAnalytics/protector-model/seeds/funnel_spec.yml \
  --out /Users/zachrybreeden/Desktop/FourTwentyAnalytics/protector-model/signals/funnel_progress.json \
  --control-flow-target 150
```

Notes & dependencies:

- The script requires PyYAML (`yaml`) to parse seeds. Install via pip if missing: `pip3 install pyyaml`.
- The generator writes the CSV summary to `data/internal/log.report.csv` to match other module generators and to make downstream inspection/automation easier.

---

*This star is part of the FourTwenty Analytics constellation - a modular analytics sandbox where each repository is a specialized "model" within an orbital system.*
