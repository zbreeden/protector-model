#!/usr/bin/env python3
import csv, random, re, sys
from datetime import datetime

src = "clean_base.csv"
dst = "raw_pen_paper_intake.csv"
if len(sys.argv) > 1: src = sys.argv[1]
if len(sys.argv) > 2: dst = sys.argv[2]

def rand_date_variants(iso_str):
    # Turn "2025-02-03" into inconsistent pen-and-paper formats
    try:
        d = datetime.strptime(iso_str, "%Y-%m-%d")
        choices = [
            d.strftime("%m/%d/%Y"),
            d.strftime("%-m/%-d/%y") if hasattr(d, "strftime") else d.strftime("%m/%d/%y"),
            d.strftime("%d-%b-%Y"),
            d.strftime("%Y/%m/%d"),
        ]
        # ~5% deliberately invalid like 02-31-2025
        if random.random() < 0.05:
            return "02-31-2025"
        return random.choice(choices)
    except:
        return iso_str

def messy_phone(s):
    # Mix raw digits, dashes, parens, spaces
    if random.random() < 0.3:  # leave as-is sometimes
        return s
    digits = re.sub(r"\D+", "", s)
    formats = [f"({digits[:3]}) {digits[3:6]}-{digits[6:]}",
               f"{digits[:3]}-{digits[3:6]}-{digits[6:]}",
               f"{digits[:3]}.{digits[3:6]}.{digits[6:]}",
               f"{digits}"]
    return random.choice(formats)

def abbreviate(addr):
    # Route → rt., Avenue → Ave, Road → Rd, Street → St
    addr = re.sub(r"\bRoute\b", "rt.", addr, flags=re.I)
    addr = re.sub(r"\bAvenue\b", "Ave", addr, flags=re.I)
    addr = re.sub(r"\bRoad\b", "Rd", addr, flags=re.I)
    addr = re.sub(r"\bStreet\b", "St", addr, flags=re.I)
    return addr

def occasional_typo(city):
    # Hamilton → Hamilt0n etc (~6%)
    if city.lower() == "hamilton" and random.random() < 0.06:
        return "Hamilt0n"
    return city

random.seed(17)

with open(src, newline="", encoding="utf-8") as f_in, open(dst, "w", newline="", encoding="utf-8") as f_out:
    rows = list(csv.DictReader(f_in))
    # Simulate header oddities: rename some headers, add an extra freeform column
    fieldnames = ["Site Name","Address","City","State","Zip","Contact","Phone","System","Last Inspection","Notes","Extra Notes"]
    w = csv.DictWriter(f_out, fieldnames=fieldnames)
    w.writeheader()

    for r in rows:
        out = {
            "Site Name": r["site_name"].upper() if random.random()<0.15 else r["site_name"],  # random casing
            "Address": abbreviate(r["address_line1"]).strip() + ("  " if random.random()<0.1 else ""),  # stray spaces
            "City": occasional_typo(r["city"]),
            "State": r["state"],
            "Zip": r["zip"],
            "Contact": f'{r["contact_last"]}, {r["contact_first"]}',
            "Phone": messy_phone(r["phone_raw"]),
            "System": r["system_type"],
            "Last Inspection": rand_date_variants(r["last_inspection_dt"]),
            "Notes": r["note"],
            "Extra Notes": "" if random.random()<0.7 else "Left form on clip board",
        }
        # Insert a duplicate row sometimes (~3%)
        w.writerow(out)
        if random.random() < 0.03:
            w.writerow(out)

print(f"Wrote messy pen-and-paper file to {dst}")

