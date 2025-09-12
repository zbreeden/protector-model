
import pandas as pd, re, json, yaml, sys, uuid
from datetime import datetime
from pathlib import Path

def std_phone(s):
    digits = re.sub(r"\D", "", str(s))
    if len(digits)==10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    return s

def parse_address(addr, fallback_state="OH"):
    # naive parse; split city/state/zip if present, otherwise leave blanks
    addr = str(addr)
    # Normalize common abbreviations
    addr = addr.replace(" rt.", " Route ").replace("Wy.", " Way").replace("Cinti", "Cincinnati")
    parts = re.split(r",\s*", addr)
    line1 = parts[0].strip() if parts else ""
    city, state, postal = "", fallback_state, ""
    if len(parts) >= 2:
        # try to get city + state + zip from remaining
        tail = " ".join(parts[1:])
        m = re.search(r"([A-Za-z ]+)\s+([A-Z]{2})\s+(\d{5})", tail)
        if m:
            city, state, postal = m.group(1).title().strip(), m.group(2), m.group(3)
        else:
            # try city only
            city = parts[1].title().strip()
    return line1, city, state, postal

def infer_products(equip_notes, patterns):
    result = []
    txt = str(equip_notes).lower()
    for k, code in patterns.items():
        if k.lower() in txt:
            result.append(code)
    return list(set(result)) or ["UNKNOWN_ASSET"]

def severity_from_notes(notes, sev_cfg):
    txt = str(notes).lower()
    for sev, keywords in sev_cfg.items():
        for kw in keywords:
            if kw in txt:
                return sev
    return "C"

def normalize(df, cfg):
    fixes = cfg["parsing_rules"]["fix_common_typos"]
    freq_map = cfg["parsing_rules"]["maintenance_frequency_map"]
    products = cfg["parsing_rules"]["product_inference"]["patterns"]
    fallback_state = cfg["defaults"]["StateFallback"]
    country = cfg["defaults"]["Country"]
    silco_branch = cfg["defaults"]["SilcoBranch"]
    territory = cfg["defaults"]["Territory"]

    rows_sites = []
    rows_assets = []
    rows_plans = []
    rows_wos = []
    rows_insp = []
    rows_def = []

    account_id = f"A-{uuid.uuid4().hex[:6].upper()}"
    for _, r in df.iterrows():
        county = fixes.get(str(r["CountyRaw"]), str(r["CountyRaw"]))
        addr1, city, state, postal = parse_address(r["AddressRaw"], fallback_state)
        phone = std_phone(r["PhoneRaw"])

        site_id = f"S-{uuid.uuid4().hex[:6].upper()}"
        rows_sites.append({
            "SiteId__c": site_id,
            "AccountId": account_id,
            "SiteName__c": r["SiteNameRaw"],
            "Address__c": addr1,
            "City__c": city,
            "State__c": state,
            "PostalCode__c": postal,
            "County__c": county,
            "Phone__c": phone,
            "SilcoBranch__c": silco_branch,
            "Territory__c": territory,
            "PaperDocId__c": r["PaperDocId"]
        })

        product_codes = infer_products(r["EquipNotesRaw"], products)
        for pc in product_codes:
            asset_id = f"AS-{uuid.uuid4().hex[:6].upper()}"
            rows_assets.append({
                "AssetId": asset_id,
                "AccountId": account_id,
                "SiteId__c": site_id,
                "ProductCode": pc,
                "SerialNumber": "",
                "InstallDate": pd.to_datetime(r["InstallDateRaw"], errors="coerce").date() if pd.notna(r["InstallDateRaw"]) else None,
                "Status": "In Service"
            })
            # Maintenance plan per product (simplified)
            mp_id = f"MP-{uuid.uuid4().hex[:6].upper()}"
            freq_tokens = [t.strip().lower() for t in str(r["MaintenancePlanRaw"]).replace(";",",").split(",")]
            freq = "Annual"
            for t in freq_tokens:
                if t in freq_map:
                    freq = freq_map[t]
            rows_plans.append({
                "MaintenancePlanId__c": mp_id,
                "AccountId": account_id,
                "SiteId__c": site_id,
                "AssetId": asset_id,
                "PlanName__c": f"{pc} - {freq}",
                "Frequency__c": freq,
                "NextDueDate__c": pd.to_datetime("today").normalize()  # demo
            })

        # Create Work Order & Inspection from last inspection notes
        wo_id = f"WO-{uuid.uuid4().hex[:6].upper()}"
        rows_wos.append({
            "WorkOrderId": wo_id,
            "AccountId": account_id,
            "SiteId__c": site_id,
            "Type": "Acquisition Intake",
            "Subject": "Initial safety & compliance baseline",
            "Priority": "High",
            "Status": "Open",
            "CreatedDate": pd.to_datetime("today").normalize(),
            "DueDate": pd.to_datetime("today").normalize() + pd.Timedelta(days=7)
        })

        insp_id = f"INSP-{uuid.uuid4().hex[:6].upper()}"
        rows_insp.append({
            "InspectionId__c": insp_id,
            "WorkOrderId": wo_id,
            "InspectionDate__c": pd.to_datetime(r["LastInspectionRaw"], errors="coerce").date(),
            "Inspector__c": "TBD",
            "Standard__c": "NFPA 25/72",
            "PassFail__c": "Fail" if isinstance(r["LastInspectionRaw"], str) and "02-31" in r["LastInspectionRaw"] else "Unknown",
            "Notes__c": r["DeficiencyNotesRaw"]
        })

        sev = severity_from_notes(r["DeficiencyNotesRaw"], cfg["severity_scoring"])
        def_id = f"DEF-{uuid.uuid4().hex[:6].upper()}"
        rows_def.append({
            "DeficiencyId__c": def_id,
            "WorkOrderId": wo_id,
            "Severity__c": sev,
            "CodeReference__c": "",
            "Description__c": r["DeficiencyNotesRaw"],
            "RecommendedAction__c": "Technician assessment, generate quote",
            "QuotedAmount__c": None,
            "Status__c": "Open"
        })

    return (
        pd.DataFrame(rows_sites),
        pd.DataFrame(rows_assets),
        pd.DataFrame(rows_plans),
        pd.DataFrame(rows_wos),
        pd.DataFrame(rows_insp),
        pd.DataFrame(rows_def)
    )

def quality_report(df):
    issues = []
    for i, r in df.iterrows():
        if pd.isna(pd.to_datetime(r.get("LastInspectionRaw", None), errors="coerce")):
            issues.append(("LastInspectionRaw", i, str(r.get("LastInspectionRaw"))))
        if "Hamilt0n" in str(r.get("CountyRaw")):
            issues.append(("CountyRaw", i, "typo->Hamilton"))
        if any(k in str(r.get("AddressRaw")).lower() for k in ["rt.", "wy."]):
            issues.append(("AddressRaw", i, "abbrev present"))
    rep = pd.DataFrame(issues, columns=["Field","RowIndex","Issue"])
    return rep

def main():
    in_csv = Path(sys.argv[1]) if len(sys.argv)>1 else Path("raw_pen_paper_intake.csv")
    cfg_path = Path(sys.argv[2]) if len(sys.argv)>2 else Path("mapping_config.yml")
    out_dir = Path(sys.argv[3]) if len(sys.argv)>3 else Path("normalized_out")
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_csv)
    with open(cfg_path, "r") as f:
        cfg = yaml.safe_load(f)

    # Quality report first (for demo)
    q = quality_report(df)
    q.to_csv(out_dir/"quality_report.csv", index=False)

    sites, assets, plans, wos, insps, defs = normalize(df, cfg)
    sites.to_csv(out_dir/"sites__c.csv", index=False)
    assets.to_csv(out_dir/"assets.csv", index=False)
    plans.to_csv(out_dir/"maintenance_plans__c.csv", index=False)
    wos.to_csv(out_dir/"work_orders.csv", index=False)
    insps.to_csv(out_dir/"inspections__c.csv", index=False)
    defs.to_csv(out_dir/"deficiencies__c.csv", index=False)

    print("Wrote normalized outputs and quality_report.csv to", out_dir)

if __name__ == "__main__":
    main()
