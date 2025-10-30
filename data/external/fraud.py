
"""Synthetic fraud dataset generator.

Reads `fraud.specs.json` (same directory) and writes relational CSVs:
customer.csv, account.csv, device.csv, merchant.csv, login_event.csv,
txn.csv, case_link.csv, case_alert.csv.

Usage:
	python fraud.py --spec fraud.specs.json --out-dir . --seed 42

Options:
	--spec      Path to specs JSON (default: fraud.specs.json)
	--out-dir   Directory to write CSVs (default: current dir)
	--seed      Deterministic random seed (optional)
	--dry-run   Generate smaller dataset (for quick tests)

The script uses Faker for fake names/ips and only the Python stdlib otherwise.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

from faker import Faker


def poisson(lmbda: float) -> int:
	# Knuth algorithm
	L = math.exp(-lmbda)
	k = 0
	p = 1.0
	while p > L:
		k += 1
		p *= random.random()
	return max(0, k - 1)


def iso(dt: datetime) -> str:
	return dt.replace(tzinfo=timezone.utc).isoformat()


def make_dirs(path: Path) -> None:
	path.mkdir(parents=True, exist_ok=True)


def generate(spec_path: Path, out_dir: Path, seed: int | None = None, dry_run: bool = False) -> Dict[str, int]:
	if seed is not None:
		random.seed(seed)
		Faker.seed(seed)

	faker = Faker()

	specs = json.loads(spec_path.read_text())

	# optionally shrink counts for dry-run
	shrink = 0.02 if dry_run else 1.0

	n_customers = max(1, int(specs.get("n_customers", 5000) * shrink))
	n_devices_mean = specs.get("n_devices_per_customer_mean", 1.3)
	n_accounts_mean = specs.get("n_accounts_per_customer_mean", 1.2)
	txn_days = specs.get("txn_days", 60)
	txns_per_day_mean = specs.get("txns_per_day_mean", 2500)
	fraud_rate = specs.get("fraud_rate", 0.005)
	geo_mismatch_rate = specs.get("geo_mismatch_rate", 0.02)
	low_rep_device_rate = specs.get("low_rep_device_rate", 0.04)
	high_amount_rate = specs.get("high_amount_rate", 0.03)
	channels = specs.get("channels", ["card_present", "ecommerce", "ach", "wire"])
	countries = specs.get("countries", ["US", "CA", "GB", "DE", "IN"])

	# Create out dir
	make_dirs(out_dir)

	# Customers
	customers: List[Dict] = []
	for cid in range(1, n_customers + 1):
		first_seen = faker.date_time_between(start_date='-2y', end_date='now', tzinfo=timezone.utc)
		customers.append({
			"customer_id": cid,
			"person_hash": faker.sha256(raw_output=False),
			"first_seen_ts": iso(first_seen),
			"kyc_status": random.choice(["passed", "pending", "failed"]),
			"pep_flag": random.choice(["Y", "N"]),
			"sanctions_hit": random.choice(["", "OFAC"]).strip(),
			"record_src": random.choice(["sim", "import"]),
			"created_at": iso(first_seen)
		})

	# Accounts
	accounts: List[Dict] = []
	aid = 1
	for c in customers:
		n_acc = max(1, poisson(n_accounts_mean))
		for _ in range(n_acc):
			open_dt = faker.date_between(start_date='-2y', end_date='today')
			accounts.append({
				"account_id": aid,
				"customer_id": c["customer_id"],
				"product_type": random.choice(["checking", "savings", "credit", "loan"]),
				"open_dt": open_dt.isoformat(),
				"status": random.choice(["open", "closed", "dormant"]),
				"created_at": iso(datetime.utcnow())
			})
			aid += 1

	# Devices
	devices: List[Dict] = []
	did = 1
	for c in customers:
		n_dev = max(1, poisson(n_devices_mean))
		for _ in range(n_dev):
			first_seen = faker.date_time_between(start_date='-2y', end_date='now', tzinfo=timezone.utc)
			risk_rep = random.choice(["low", "medium", "high"]) if random.random() > low_rep_device_rate else "low"
			devices.append({
				"device_id": did,
				"device_fingerprint": faker.uuid4(),
				"first_seen_ts": iso(first_seen),
				"risk_reputation": risk_rep,
				"last_ip": faker.ipv4_public(),
				"last_country": random.choice(countries),
				"created_at": iso(first_seen)
			})
			did += 1

	# Map customers to devices (at least one per customer)
	cust_devices: Dict[int, List[int]] = defaultdict(list)
	device_index = 0
	for c in customers:
		# give each customer at least one device, optionally more
		devs_for_customer = 1 + random.randint(0, 1)
		for _ in range(devs_for_customer):
			# wrap index
			device_index = device_index % len(devices)
			cust_devices[c["customer_id"]].append(devices[device_index]["device_id"])
			device_index += 1

	# Merchants
	merchants: List[Dict] = []
	n_merchants = max(50, int(0.02 * (txns_per_day_mean * txn_days) * shrink))
	for mid in range(1, n_merchants + 1):
		merchants.append({
			"merchant_id": mid,
			"mcc": random.choice(["5311", "5411", "5812", "5999", "6011"]),
			"name": faker.company(),
			"country": random.choice(countries),
			"risk_tag": random.choice(["low", "medium", "high"]),
			"created_at": iso(faker.date_time_between(start_date='-5y', end_date='now', tzinfo=timezone.utc))
		})

	# Login events
	logins: List[Dict] = []
	login_id = 1
	for c in customers:
		n_logins = max(1, poisson(2.0))
		for _ in range(n_logins):
			device_id = random.choice(cust_devices[c["customer_id"]])
			login_ts = faker.date_time_between(start_date='-90d', end_date='now', tzinfo=timezone.utc)
			logins.append({
				"login_id": login_id,
				"customer_id": c["customer_id"],
				"device_id": device_id,
				"login_ts": iso(login_ts),
				"ip": faker.ipv4_public(),
				"country": random.choice(countries),
				"success": random.choice([True, False, True, True]),
				"mfa_passed": random.choice([True, False, True]),
				"created_at": iso(login_ts)
			})
			login_id += 1

	# Transactions
	txns: List[Dict] = []
	txn_id = 1
	start_date = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=txn_days)
	total_days = txn_days
	for day in range(total_days):
		# number of txns this day
		n_today = poisson(txns_per_day_mean * shrink)
		day_base = start_date + timedelta(days=day)
		for _ in range(n_today):
			# choose account, customer, merchant
			acct = random.choice(accounts)
			cust_id = acct["customer_id"]
			# device may be from customer's devices
			device_id = random.choice(cust_devices[cust_id])
			merchant = random.choice(merchants)
			# timestamp within the day
			t = day_base + timedelta(seconds=random.randint(0, 86399))
			# amount in cents
			if random.random() < high_amount_rate:
				amount = random.randint(20000, 200000)  # $200 - $2000
			else:
				amount = random.randint(100, 20000)  # $1 - $200

			country = random.choice(countries)

			# fraud label (ground truth)
			is_fraud = random.random() < fraud_rate

			# create geo mismatch occasionally
			if random.random() < geo_mismatch_rate:
				country = random.choice([c for c in countries if c != country])

			txns.append({
				"txn_id": txn_id,
				"account_id": acct["account_id"],
				"customer_id": cust_id,
				"merchant_id": merchant["merchant_id"],
				"txn_ts": iso(t),
				"amount_cents": amount,
				"currency": random.choice(["USD", "CAD", "GBP", "EUR", "INR"]),
				"channel": random.choice(channels),
				"device_id": device_id,
				"ip": faker.ipv4_public(),
				"country": country,
				"auth_result": random.choice(["approved", "declined", "blocked"]),
				"label_fraud": int(is_fraud),
				"chargeback_flag": int(is_fraud and random.random() < 0.15),
				"created_at": iso(datetime.utcnow())
			})
			txn_id += 1

	# Cases: create some cases linked to fraudulent or high-risk txns
	case_links: List[Dict] = []
	case_alerts: List[Dict] = []
	case_id = 1
	# pick up to 1% of txns as cases, biased to fraud
	candidate_txns = [t for t in txns if t["label_fraud"] == 1]
	# add some non-fraud suspicious
	candidate_txns += random.sample(txns, min(len(txns), max(1, int(0.001 * len(txns)))))

	for t in candidate_txns[: max(1, int(0.01 * len(txns)) )]:
		case_links.append({
			"case_id": case_id,
			"txn_id": t["txn_id"]
		})
		opened = datetime.utcnow() - timedelta(days=random.randint(0, 30))
		case_alerts.append({
			"case_id": case_id,
			"opened_ts": iso(opened),
			"status": random.choice(["open", "closed", "investigating"]),
			"priority": random.choice(["low", "medium", "high"]),
			"reason_code": random.choice(["fraud", "chargeback", "kyc"]),
			"risk_score": random.randint(10, 99),
			"assigned_to": random.choice(["analyst_1", "analyst_2", "auto"]),
			"created_at": iso(opened)
		})
		case_id += 1

	# Write CSVs with headers matching attachments
	def write_csv(path: Path, rows: List[Dict], headers: List[str]):
		with path.open("w", newline='') as fh:
			w = csv.DictWriter(fh, fieldnames=headers)
			w.writeheader()
			for r in rows:
				# ensure all headers present
				out = {h: r.get(h, "") for h in headers}
				w.writerow(out)

	# paths
	write_csv(out_dir / "customer.csv", customers, [
		"customer_id",
		"person_hash",
		"first_seen_ts",
		"kyc_status",
		"pep_flag",
		"sanctions_hit",
		"record_src",
		"created_at",
	])

	write_csv(out_dir / "account.csv", accounts, [
		"account_id",
		"customer_id",
		"product_type",
		"open_dt",
		"status",
		"created_at",
	])

	write_csv(out_dir / "device.csv", devices, [
		"device_id",
		"device_fingerprint",
		"first_seen_ts",
		"risk_reputation",
		"last_ip",
		"last_country",
		"created_at",
	])

	write_csv(out_dir / "merchant.csv", merchants, [
		"merchant_id",
		"mcc",
		"name",
		"country",
		"risk_tag",
		"created_at",
	])

	write_csv(out_dir / "login_event.csv", logins, [
		"login_id",
		"customer_id",
		"device_id",
		"login_ts",
		"ip",
		"country",
		"success",
		"mfa_passed",
		"created_at",
	])

	write_csv(out_dir / "txn.csv", txns, [
		"txn_id",
		"account_id",
		"customer_id",
		"merchant_id",
		"txn_ts",
		"amount_cents",
		"currency",
		"channel",
		"device_id",
		"ip",
		"country",
		"auth_result",
		"label_fraud",
		"chargeback_flag",
		"created_at",
	])

	write_csv(out_dir / "case_link.csv", case_links, [
		"case_id",
		"txn_id",
	])

	write_csv(out_dir / "case_alert.csv", case_alerts, [
		"case_id",
		"opened_ts",
		"status",
		"priority",
		"reason_code",
		"risk_score",
		"assigned_to",
		"created_at",
	])

	stats = {
		"customers": len(customers),
		"accounts": len(accounts),
		"devices": len(devices),
		"merchants": len(merchants),
		"logins": len(logins),
		"txns": len(txns),
		"cases": len(case_alerts),
	}

	# run integrity check and write manifest
	integrity = run_integrity_checks(out_dir)
	write_manifest(out_dir, stats)
	# write integrity report as JSON
	import json as _json
	(out_dir / 'integrity_report.json').write_text(_json.dumps(integrity, indent=2))

	return stats


def main() -> None:
	p = argparse.ArgumentParser(description="Generate synthetic fraud CSVs")
	p.add_argument("--spec", default="fraud.specs.json", help="spec JSON file path")
	p.add_argument("--out-dir", default=".", help="output directory for CSVs")
	p.add_argument("--seed", type=int, default=None, help="random seed for deterministic output")
	p.add_argument("--dry-run", action="store_true", help="generate small sample for testing")
	args = p.parse_args()

	spec_path = Path(args.spec)
	out_dir = Path(args.out_dir)

	if not spec_path.exists():
		raise SystemExit(f"Spec file not found: {spec_path}")

	stats = generate(spec_path, out_dir, seed=args.seed, dry_run=args.dry_run)
	print("Wrote CSVs to", out_dir)
	for k, v in stats.items():
		print(f"  {k}: {v}")


def write_manifest(out_dir: Path, stats: Dict[str, int]) -> None:
	"""Write a README.csv manifest with file, rows, and size_bytes."""
	import csv, os
	rows = []
	for name in [
		'customer.csv', 'account.csv', 'device.csv', 'merchant.csv',
		'login_event.csv', 'txn.csv', 'case_link.csv', 'case_alert.csv']:
		p = out_dir / name
		if p.exists():
			size = p.stat().st_size
			# read rowcount quickly
			with p.open() as fh:
				rowcount = sum(1 for _ in fh)
		else:
			size = 0
			rowcount = 0
		rows.append({'file': name, 'rows': rowcount, 'size_bytes': size})
	with (out_dir / 'README.csv').open('w', newline='') as fh:
		w = csv.DictWriter(fh, fieldnames=['file', 'rows', 'size_bytes'])
		w.writeheader()
		for r in rows:
			w.writerow(r)


def run_integrity_checks(out_dir: Path) -> Dict:
	"""Run the same checks as check_integrity.py and return a dict of results."""
	import csv
	from collections import defaultdict

	def load_key_set(path: Path, key: str):
		s = set()
		with path.open() as fh:
			r = csv.DictReader(fh)
			for row in r:
				s.add(row.get(key, ''))
		return s

	def find_missing(parent: set, child_path: Path, fk: str):
		missing = 0
		examples = []
		with child_path.open() as fh:
			r = csv.DictReader(fh)
			for row in r:
				val = row.get(fk, '')
				if val == '' or val not in parent:
					missing += 1
					if len(examples) < 5:
						examples.append(row)
		return {'count_missing_values': missing, 'examples': examples}

	d = out_dir

	customer_keys = load_key_set(d / 'customer.csv', 'customer_id')
	account_keys = load_key_set(d / 'account.csv', 'account_id')
	device_keys = load_key_set(d / 'device.csv', 'device_id')
	merchant_keys = load_key_set(d / 'merchant.csv', 'merchant_id')
	txn_keys = load_key_set(d / 'txn.csv', 'txn_id')

	results = {}
	results['account.customer_id'] = find_missing(customer_keys, d / 'account.csv', 'customer_id')
	results['login_event.customer_id'] = find_missing(customer_keys, d / 'login_event.csv', 'customer_id')
	results['login_event.device_id'] = find_missing(device_keys, d / 'login_event.csv', 'device_id')
	results['txn.account_id'] = find_missing(account_keys, d / 'txn.csv', 'account_id')
	results['txn.customer_id'] = find_missing(customer_keys, d / 'txn.csv', 'customer_id')
	results['txn.merchant_id'] = find_missing(merchant_keys, d / 'txn.csv', 'merchant_id')
	results['txn.device_id'] = find_missing(device_keys, d / 'txn.csv', 'device_id')
	results['case_link.txn_id'] = find_missing(txn_keys, d / 'case_link.csv', 'txn_id')

	# reduce examples to only small dicts to keep JSON small
	for k, v in results.items():
		v['examples'] = [{kk: vv for kk, vv in ex.items()} for ex in v['examples']]

	return results


if __name__ == "__main__":
	main()
