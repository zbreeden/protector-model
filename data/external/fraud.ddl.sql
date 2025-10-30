CREATE VIEW v_feat_velocity AS
SELECT t.txn_id, t.customer_id, t.txn_ts,
       COUNT(*) OVER (
         PARTITION BY t.customer_id
         ORDER BY t.txn_ts
         RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND CURRENT ROW
       ) AS tx_30m_cnt
FROM Txn t;

CREATE VIEW v_feat_geo AS
WITH last_login AS (
  SELECT l.customer_id, l.country AS login_country, l.login_ts,
         ROW_NUMBER() OVER (PARTITION BY l.customer_id ORDER BY l.login_ts DESC) rn
  FROM LoginEvent l
)
SELECT t.txn_id, t.customer_id, t.country AS txn_country, ll.login_country,
       (ll.login_country IS DISTINCT FROM t.country) AS geo_mismatch
FROM Txn t
LEFT JOIN last_login ll
  ON ll.customer_id=t.customer_id AND ll.rn=1
  AND t.txn_ts BETWEEN ll.login_ts AND ll.login_ts + INTERVAL '2 hour';

CREATE VIEW v_feat_device AS
SELECT t.txn_id, COALESCE((d.risk_reputation <= 20),false) AS device_low_rep
FROM Txn t LEFT JOIN Device d ON d.device_id=t.device_id;

CREATE VIEW v_risk_event AS
SELECT t.txn_id, t.customer_id, t.account_id, t.txn_ts,
  (CASE WHEN v.tx_30m_cnt>=5 THEN 20 ELSE 0 END)
+ (CASE WHEN g.geo_mismatch THEN 30 ELSE 0 END)
+ (CASE WHEN d.device_low_rep THEN 25 ELSE 0 END)
+ (CASE WHEN t.channel='ecommerce' THEN 10 ELSE 0 END)
+ (CASE WHEN t.amount_cents>500000 THEN 15 ELSE 0 END) AS rule_score
FROM Txn t
LEFT JOIN v_feat_velocity v ON v.txn_id=t.txn_id
LEFT JOIN v_feat_geo g      ON g.txn_id=t.txn_id
LEFT JOIN v_feat_device d   ON d.txn_id=t.txn_id;

CREATE VIEW fact_risk AS
SELECT r.txn_id, r.customer_id, r.account_id, r.txn_ts::date AS date_key, r.rule_score
FROM v_risk_event r;

CREATE VIEW fact_txn AS
SELECT txn_id, customer_id, account_id, merchant_id, txn_ts::date AS date_key,
       amount_cents/100.0 AS amount, currency, channel, label_fraud, chargeback_flag
FROM Txn;

CREATE VIEW dim_customer AS
SELECT customer_id, person_hash, kyc_status, pep_flag, sanctions_hit, first_seen_ts::date AS first_seen_dt
FROM Customer;

CREATE VIEW dim_account AS
SELECT account_id, customer_id, product_type, status, open_dt FROM Account;

CREATE VIEW dim_merchant AS
SELECT merchant_id, mcc, name, country, risk_tag FROM Merchant;