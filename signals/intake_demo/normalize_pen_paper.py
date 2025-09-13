#!/usr/bin/env python3
"""
normalize_pen_paper.py
Turn messy pen-and-paper CSV into normalized, Salesforce-shaped tables + quality report.

Usage:
  python3 normalize_pen_paper.py raw_pen_paper_intake.csv mapping_config.yml normalized_out/
"""
import sys, re, json, uuid
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Dict, Any

import pandas as pd

try:
    import yaml
except Exception:
    yaml = None  # We'll allow running with a built-in default config if PyYAML is missing.


# ------------------------------
# Helpers
# ------------------------------
def _strip(s):
    return None if pd.isna(s) else str(s).strip()


def std_phone(s: Any) -> Any:
    digits = re.sub(r"\D", "", str(s or ""))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return s


def parse_date_fuzzy(s: Any) -> Tuple[Any, bool]:
    """Return (standardized_date_iso, valid_bool). Keep None when invalid."""
    if s is None or (isinstance(s, float) and pd.isna(s)) or str(s).strip() == "":
        return None, True  # empty is allowed; not an error
    text = str(s).strip()
    # Try a handful of common formats
    fmts = ["%m/%d/%Y", "%-m/%-d/%Y", "%m/%d/%y", "%Y/%m/%d", "%Y-%m-%d", "%d-%b-%Y"]
    for fmt in fmts:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y-%m-%d"), True
        except Exception:
            continue
    return None, False


def normalize_address(addr: Any) -> str:
    """Normalize common road abbreviations; keep it simple for demo."""
    s = str(addr or "")
    repl = {
        r"\brt\.?\b": "Route",
        r"\bRd\.?\b": "Road",
        r"\bSt\.?\b": "Street",
        r"\bAve\.?\b": "Avenue",
        r"\bHwy\.?\b": "Highway",
        r"\bWy\.?\b": "Way",
    }
    for pat, sub in repl.items():
        s = re.sub(pat, sub, s, flags=re.IGNORECASE)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def fix_common_typos(s: Any) -> Any:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return s
    m = {
        "Hamilt0n": "Hamilton",
        "Cinti": "Cincinnati",
    }
    return m.get(str(s), s)


def load_config(path: Path) -> Dict[str, Any]:
    defaults = {
        "defaults": {
            "Country": "USA",
            "StateFallback": "OH",
            "SilcoBranch": "Cincinnati",
            "Territory": "Southwest OH",
        },
        "lookups": {
            "city_to_county": {
                "Cincinnati": "Hamilton",
                "Hamilton": "Butler",
                "Mason": "Warren",
                "Dayton": "Montgomery",
                "Columbus": "Franklin",
            },
            "zip_to_county": {
                "45202": "Hamilton",
                "45011": "Butler",
                "45040": "Warren",
                "45402": "Montgomery",
                "43215": "Franklin",
            },
        },
        "parsing_rules": {
            "maintenance_frequency_map": {
                "qtrly": "Quarterly",
                "quarterly": "Quarterly",
                "semi": "Semiannual",
                "semiannual": "Semiannual",
                "annual": "Annual",
            },
            "product_inference": {
                "patterns": {
                    "sprinkler": "SPRINKLER_WET",
                    "ansul": "ANSUL_KITCHEN",
                    "alarm": "FIRE_ALARM",
                }
            },
        },
    }
    if path and path.exists() and yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        # shallow-merge with defaults
        def merge(a, b):
            for k, v in b.items():
                if isinstance(v, dict):
                    a[k] = merge(a.get(k, {}), v)
                else:
                    a.setdefault(k, v)
            return a
        return merge(cfg, defaults)
    return defaults


def ensure_required_columns(df: pd.DataFrame, cfg: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Backfill/derive columns that may be missing and log issues."""
    issues: List[Dict[str, Any]] = []

    # Normalize header variants for common fields
    header_aliases = {
        "Site Name": ["Site Name", "SiteName", "Name"],
        "Address": ["Address", "AddressRaw", "Street"],
        "City": ["City", "Town"],
        "State": ["State", "ST"],
        "Zip": ["Zip", "Postal", "PostalCode", "ZIP"],
        "Phone": ["Phone", "PhoneRaw", "Phone Number"],
        "Last Inspection": ["Last Inspection", "LastInspection", "LastInspectionRaw"],
        "CountyRaw": ["CountyRaw", "County"],
        "Notes": ["Notes", "Note", "Comment"],
        "System": ["System", "SystemType", "Type"],
        "Contact": ["Contact", "Contact Name", "ContactName"],
    }

    # Build a new DF with canonical headers where possible
    newcols = {}
    for canon, candidates in header_aliases.items():
        for c in candidates:
            if c in df.columns:
                newcols[canon] = df[c]
                break

    # Create missing canon columns with NA
    for canon in header_aliases.keys():
        if canon not in newcols:
            newcols[canon] = pd.Series(pd.NA, index=df.index)

    ndf = pd.DataFrame(newcols)

    # Required minimal columns for the pipeline
    required = ["Site Name", "Address", "City", "State", "Zip"]
    missing = [c for c in required if c not in ndf.columns or ndf[c].isna().all()]
    if missing:
        raise ValueError(f"Missing required column(s) with data: {missing}")

    # Backfill CountyRaw if missing
    if "CountyRaw" not in df.columns or ndf["CountyRaw"].isna().any():
        city_to_county = (cfg.get("lookups", {}) or {}).get("city_to_county", {})
        zip_to_county = (cfg.get("lookups", {}) or {}).get("zip_to_county", {})
        before_missing = int(ndf["CountyRaw"].isna().sum())
        # ZIP first
        ndf.loc[ndf["CountyRaw"].isna() & ndf["Zip"].notna(), "CountyRaw"] = (
            ndf.loc[ndf["Zip"].notna(), "Zip"].astype(str).map(zip_to_county)
        )
        # City next
        mask = ndf["CountyRaw"].isna() & ndf["City"].notna()
        ndf.loc[mask, "CountyRaw"] = ndf.loc[mask, "City"].astype(str).map(city_to_county)
        after_missing = int(ndf["CountyRaw"].isna().sum())
        if before_missing > 0:
            issues.append({
                "issue_type": "missing_column_backfilled",
                "column": "CountyRaw",
                "strategy": "zip→county, city→county",
                "rows_filled": before_missing - after_missing,
                "rows_unresolved": after_missing,
            })

    # Standardize fields
    ndf["Site Name"] = ndf["Site Name"].map(lambda s: _strip(s).upper() if s and str(s).isupper() else _strip(s))
    ndf["Address"] = ndf["Address"].map(normalize_address)
    ndf["City"] = ndf["City"].map(fix_common_typos)
    ndf["Phone"] = ndf["Phone"].map(std_phone)

    # Dates
    std_dates = []
    date_issues = 0
    for v in ndf["Last Inspection"]:
        d, ok = parse_date_fuzzy(v)
        if not ok and (not pd.isna(v)) and (str(v).strip() != ""):
            date_issues += 1
        std_dates.append(d)
    ndf["LastInspection"] = std_dates

    if date_issues:
        issues.append({
            "issue_type": "invalid_date",
            "column": "Last Inspection",
            "rows_affected": date_issues,
            "action": "flagged; kept NULL in normalized output"
        })

    return ndf, issues


def infer_products(notes: str, patterns: Dict[str, str]) -> List[str]:
    hits = []
    if not notes:
        return hits
    t = notes.lower()
    for k, code in patterns.items():
        if k in t:
            hits.append(code)
    return sorted(set(hits))


def severity_from_text(txt: str) -> str:
    if not txt:
        return "C"
    t = txt.lower()
    if any(w in t for w in ["blocked exit", "no access", "critical", "impair", "system down", "life safety"]):
        return "A"
    if any(w in t for w in ["painted head", "minor leak", "label missing", "slow flow"]):
        return "B"
    return "C"


# ------------------------------
# Main normalization
# ------------------------------
def normalize(df: pd.DataFrame, cfg: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, List[Dict[str, Any]]]:
    cfg_defaults = cfg.get("defaults", {})
    country = cfg_defaults.get("Country", "USA")
    fallback_state = cfg_defaults.get("StateFallback", "OH")

    freq_map = (cfg.get("parsing_rules", {}) or {}).get("maintenance_frequency_map", {})
    prod_patterns = (cfg.get("parsing_rules", {}) or {}).get("product_inference", {}).get("patterns", {})

    df, pre_issues = ensure_required_columns(df, cfg)

    # Final County normalized
    county_fixed = df["CountyRaw"].map(fix_common_typos)

    # Sites
    sites_rows = []
    for i, r in df.iterrows():
        site_id = str(uuid.uuid4())
        sites_rows.append({
            "SiteId": site_id,
            "Name": _strip(r["Site Name"]),
            "Address": _strip(r["Address"]),
            "City": _strip(r["City"]),
            "State": _strip(r["State"]) or fallback_state,
            "Zip": _strip(r["Zip"]),
            "County": _strip(county_fixed.iat[i]) if not pd.isna(county_fixed.iat[i]) else None,
            "Phone": _strip(r["Phone"]),
            "Country": country,
        })
    sites = pd.DataFrame(sites_rows)

    # Assets (one per site for demo, based on System)
    assets_rows = []
    for i, r in df.iterrows():
        assets_rows.append({
            "AssetId": str(uuid.uuid4()),
            "SiteId": sites_rows[i]["SiteId"],
            "SystemType": _strip(r["System"]),
            "Serial": None,
        })
    assets = pd.DataFrame(assets_rows)

    # Maintenance Plans (infer from Notes frequency words; explode when multiple)
    plans_rows = []
    for i, r in df.iterrows():
        notes = str(_strip(r["Notes"]) or "")
        # crude extraction of tokens like "qtrly", "semi", "annual"
        tokens = re.findall(r"(qtrly|quarterly|semi|semiannual|annual)", notes, flags=re.I)
        if not tokens:
            tokens = ["annual"]
        for t in tokens:
            plans_rows.append({
                "PlanId": str(uuid.uuid4()),
                "SiteId": sites_rows[i]["SiteId"],
                "Standard": None,  # optional in this demo
                "Frequency": freq_map.get(t.lower(), t.title()),
            })
    plans = pd.DataFrame(plans_rows)

    # Work Orders — simple stub derived from LastInspection recency
    wos_rows = []
    for i, r in df.iterrows():
        wos_rows.append({
            "WOId": str(uuid.uuid4()),
            "SiteId": sites_rows[i]["SiteId"],
            "Title": "Initial Intake Cleanup",
            "DueInDays": 7 if r["LastInspection"] is None else 30,
            "Status": "Open",
        })
    wos = pd.DataFrame(wos_rows)

    # Inspections — one per site with parsed date if present
    insps_rows = []
    for i, r in df.iterrows():
        insps_rows.append({
            "InspectionId": str(uuid.uuid4()),
            "SiteId": sites_rows[i]["SiteId"],
            "InspectionDate": r["LastInspection"],
            "Result": "Needs Review" if r["LastInspection"] is None else "Complete",
        })
    insps = pd.DataFrame(insps_rows)

    # Deficiencies — infer severity from notes
    defs_rows = []
    for i, r in df.iterrows():
        sev = severity_from_text(_strip(r["Notes"]))
        defs_rows.append({
            "DeficiencyId": str(uuid.uuid4()),
            "SiteId": sites_rows[i]["SiteId"],
            "Item": _strip(r["Notes"]),
            "Severity": sev,
        })
    defs = pd.DataFrame(defs_rows)

    return sites, assets, plans, wos, insps, defs, pre_issues


def write_quality_report(issues: List[Dict[str, Any]], out_dir: Path):
    if not issues:
        q = pd.DataFrame([{"issue_type": "none", "info": "No issues recorded by pre-normalization step."}])
    else:
        q = pd.DataFrame(issues)
    q.to_csv(out_dir / "quality_report.csv", index=False)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)

    in_csv = Path(sys.argv[1])
    cfg_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else None
    out_dir = Path(sys.argv[3])

    out_dir.mkdir(parents=True, exist_ok=True)

    # Load raw CSV
    df = pd.read_csv(in_csv)

    # Load configuration (if available)
    cfg = load_config(cfg_path)

    # Normalize
    sites, assets, plans, wos, insps, defs, pre_issues = normalize(df, cfg)

    # Write tables
    sites.to_csv(out_dir / "sites__c.csv", index=False)
    assets.to_csv(out_dir / "assets.csv", index=False)
    plans.to_csv(out_dir / "maintenance_plans__c.csv", index=False)
    wos.to_csv(out_dir / "work_orders.csv", index=False)
    insps.to_csv(out_dir / "inspections__c.csv", index=False)
    defs.to_csv(out_dir / "deficiencies__c.csv", index=False)

    # Quality report
    write_quality_report(pre_issues, out_dir)

    print(f"✔ Wrote normalized outputs and quality_report.csv to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
