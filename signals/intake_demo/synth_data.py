#!/usr/bin/env python3
"""
General-purpose synthetic data generator with survey helpers.

Usage:
  python synth_data.py --spec path/to/spec.json
  # YAML supported if PyYAML is installed:
  python synth_data.py --spec path/to/spec.yml

Spec example:
{
  "output": "out.csv",
  "rows": 1000,
  "seed": 42,
  "columns": {
    "id": {"type": "uuid"},
    "dt": {"type": "datetime", "start": "2024-01-01", "end": "2025-12-31", "fmt": "%Y-%m-%d %H:%M:%S"},
    "score": {"type": "likert5"},
    "topics": {"type": "multichoice", "values": ["A","B","C"], "min_k": 1, "max_k": 2},
    "note": {"type": "derive", "template": "Score {score} on {dt}"}
  }
}

Supported 'type's:
- uuid
- int            -> {"min": 0, "max": 10}
- float          -> {"min": 0, "max": 1, "round": 2, "dist": "uniform|normal|lognormal|gamma"}
- bool           -> {"p": 0.5}  # returns 0/1
- choice         -> {"values": [...], "weights": [...]}
- multichoice    -> {"values": [...], "min_k": 1, "max_k": 3, "delimiter": ";"}
- date           -> {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "fmt": "%Y-%m-%d"}
- datetime       -> {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "fmt": "%Y-%m-%d %H:%M:%S"}
- first_name, last_name, city, state, zip
- email          -> {"domain": "example.com"}  # uses first_name/last_name if present
- lorem          -> {"words": 6}
- poisson        -> {"lam": 3}
- likert5        -> optional {"weights": [w1..w5]}
- likert7        -> optional {"weights": [w1..w7]}
- fk             -> {"source": "path/to.csv", "column": "customer_id"}
- derive         -> {"template": "string with {column} placeholders"}
"""

import argparse, csv, json, random, uuid, math, re
from datetime import datetime, timedelta
from pathlib import Path

NAMES_FIRST = [
    "Avery","Blake","Casey","Dakota","Emerson","Finley","Harper","Jordan","Kai","Logan",
    "Morgan","Peyton","Quinn","Riley","Sawyer","Taylor","Alex","Charlie","Jesse","Skyler"
]
NAMES_LAST = [
    "Smith","Johnson","Williams","Brown","Jones","Miller","Davis","Garcia","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"
]
CITIES = [
    "Cincinnati","Dayton","Columbus","Cleveland","Toledo","Akron","Louisville","Lexington","Indianapolis","Chicago"
]
STATES = ["OH","KY","IN","IL","MI","PA","WV","WI","MO","TN"]
# Prebuild some zips
random.seed(1337)
ZIPS = [f"{random.randint(10000, 99999)}" for _ in range(200)]  # prebuilt
random.seed()  # restore entropy

LOREM = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
         "incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis "
         "nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat").split()

def load_spec(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in [".yml", ".yaml"]:
        try:
            import yaml  # type: ignore
            return yaml.safe_load(text)
        except Exception as e:
            raise RuntimeError("YAML spec provided but PyYAML is not available. Install PyYAML or provide a JSON spec.") from e
    else:
        return json.loads(text)

def parse_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d")

def rand_date(start: str, end: str):
    d0 = parse_date(start)
    d1 = parse_date(end)
    if d1 < d0:
        d0, d1 = d1, d0
    delta_days = (d1 - d0).days
    return d0 + timedelta(days=random.randint(0, max(delta_days, 0)))

def rand_datetime(start: str, end: str):
    d0 = parse_date(start)
    d1 = parse_date(end)
    if d1 < d0:
        d0, d1 = d1, d0
    total_seconds = int((d1 - d0).total_seconds())
    offs = random.randint(0, max(total_seconds, 0))
    return d0 + timedelta(seconds=offs)

def weighted_choice(values, weights=None):
    if not weights:
        return random.choice(values)
    s = sum(weights)
    if s <= 0:
        return random.choice(values)
    r = random.uniform(0, s)
    upto = 0.0
    for v, w in zip(values, weights):
        upto += w
        if upto >= r:
            return v
    return values[-1]

def gen_value(kind, cfg, row_ctx, fk_cache):
    kind = (kind or "").lower()

    if kind == "uuid":
        return str(uuid.uuid4())

    if kind == "int":
        lo = int(cfg.get("min", 0))
        hi = int(cfg.get("max", 100))
        return random.randint(lo, hi)

    if kind == "float":
        dist = cfg.get("dist", "uniform")
        rnd = int(cfg.get("round", 2))
        if dist == "uniform":
            lo = float(cfg.get("min", 0.0))
            hi = float(cfg.get("max", 1.0))
            val = random.uniform(lo, hi)
        elif dist == "normal":
            mu = float(cfg.get("mean", 0.0))
            sigma = float(cfg.get("sigma", 1.0))
            val = random.gauss(mu, sigma)
        elif dist == "lognormal":
            mean = float(cfg.get("mean", 0.0))
            sigma = float(cfg.get("sigma", 1.0))
            val = random.lognormvariate(mean, sigma)
        elif dist == "gamma":
            shape = float(cfg.get("shape", 2.0))
            scale = float(cfg.get("scale", 2.0))
            val = random.gammavariate(shape, scale)
        else:
            lo = float(cfg.get("min", 0.0))
            hi = float(cfg.get("max", 1.0))
            val = random.uniform(lo, hi)
        return round(val, rnd)

    if kind == "bool":
        p = float(cfg.get("p", 0.5))
        return 1 if random.random() < p else 0

    if kind == "choice":
        values = cfg.get("values", [])
        weights = cfg.get("weights", None)
        if not values:
            return None
        return weighted_choice(values, weights)

    if kind == "multichoice":
        values = cfg.get("values", [])
        if not values:
            return ""
        min_k = int(cfg.get("min_k", 1))
        max_k = int(cfg.get("max_k", min(3, len(values))))
        if max_k > len(values):
            max_k = len(values)
        if min_k > max_k:
            min_k = max_k
        k = int(cfg.get("k", random.randint(min_k, max_k)))
        if k <= 0:
            return ""
        sample = random.sample(values, k)
        delim = cfg.get("delimiter", ";")
        return delim.join(sample)

    if kind == "date":
        start = cfg.get("start", "2024-01-01")
        end = cfg.get("end", "2025-12-31")
        fmt = cfg.get("fmt", "%Y-%m-%d")
        return rand_date(start, end).strftime(fmt)

    if kind == "datetime":
        start = cfg.get("start", "2024-01-01")
        end = cfg.get("end", "2025-12-31")
        fmt = cfg.get("fmt", "%Y-%m-%d %H:%M:%S")
        return rand_datetime(start, end).strftime(fmt)

    if kind == "first_name":
        return random.choice(NAMES_FIRST)

    if kind == "last_name":
        return random.choice(NAMES_LAST)

    if kind == "city":
        return random.choice(CITIES)

    if kind == "state":
        return random.choice(STATES)

    if kind == "zip":
        return random.choice(ZIPS)

    if kind == "email":
        domain = cfg.get("domain", "example.com")
        fn = str(row_ctx.get("first_name", "user")).lower()
        ln = str(row_ctx.get("last_name", random.randint(1000,9999))).lower()
        user = re.sub(r'[^a-z0-9]+', '.', f"{fn}.{ln}")
        return f"{user}@{domain}"

    if kind == "lorem":
        n = int(cfg.get("words", 6))
        words = [random.choice(LOREM) for _ in range(max(1, n))]
        return " ".join(words)

    if kind == "poisson":
        lam = float(cfg.get("lam", 3))
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1

    if kind == "likert5":
        values = [1,2,3,4,5]
        weights = cfg.get("weights", [0.1,0.15,0.3,0.25,0.2])
        return weighted_choice(values, weights)

    if kind == "likert7":
        values = [1,2,3,4,5,6,7]
        weights = cfg.get("weights", [0.07,0.1,0.18,0.25,0.2,0.12,0.08])
        return weighted_choice(values, weights)

    if kind == "fk":
        src = cfg["source"]
        col = cfg["column"]
        key = (src, col)
        if key not in fk_cache:
            vals = []
            with open(src, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    vals.append(r[col])
            if not vals:
                raise RuntimeError(f"Foreign key source {src} column {col} is empty")
            fk_cache[key] = vals
        return random.choice(fk_cache[key])

    if kind == "derive":
        template = cfg.get("template", "")
        try:
            return template.format(**row_ctx)
        except Exception:
            return template

    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="Path to JSON or YAML spec")
    args = ap.parse_args()

    spec_path = Path(args.spec)
    spec = load_spec(spec_path)

    seed = spec.get("seed", None)
    if seed is not None:
        random.seed(seed)

    rows = int(spec.get("rows", 1000))
    output = spec.get("output", "synthetic.csv")
    cols_cfg = spec.get("columns", {})
    col_order = list(cols_cfg.keys())

    fk_cache = {}
    out_rows = []
    for _ in range(rows):
        row_ctx = {}
        # pass 1: non-derive
        for col in col_order:
            cfg = cols_cfg[col]
            kind = str(cfg.get("type", "choice")).lower()
            if kind != "derive":
                row_ctx[col] = gen_value(kind, cfg, row_ctx, fk_cache)
        # pass 2: derive
        for col in col_order:
            cfg = cols_cfg[col]
            kind = str(cfg.get("type", "choice")).lower()
            if kind == "derive":
                row_ctx[col] = gen_value(kind, cfg, row_ctx, fk_cache)
        out_rows.append(row_ctx)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=col_order)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows to {output}")

if __name__ == "__main__":
    main()
