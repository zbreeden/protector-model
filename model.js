// Small helper: format as % with 2 decimals
const pct = x => (x*100).toFixed(2) + "%";

// Simple traffic-light class
function gradePrecision(p){ return p >= 0.9 ? "ok" : p >= 0.6 ? "warn" : "bad"; }
function gradeRecall(r){ return r >= 0.8 ? "ok" : r >= 0.5 ? "warn" : "bad"; }

async function load() {
  try {
    // If you rename the file, update this path
    const res = await fetch("./signals/baseline_metrics.json", { cache: "no-store" });
    const m = await res.json();

    // Fill values
    const prec = Number(m.precision ?? 0);
    const rec  = Number(m.recall ?? 0);
    const f1   = Number(m.f1 ?? 0);
    const thr  = Number(m.threshold ?? 0.5);
    const n    = Number(m.n_samples ?? 0);
    const ts   = m.timestamp ?? "";

    const $ = id => document.getElementById(id);
    const set = (id, val, cls) => { $(id).textContent = val; if (cls) { $(id).classList.add(cls); } };

    set("precision", pct(prec), gradePrecision(prec));
    set("recall", pct(rec), gradeRecall(rec));
    set("f1", pct(f1));
    set("threshold", (Math.round(thr*1000)/1000).toString());
    set("nsamples", n.toLocaleString());
    set("ts", new Date(ts).toLocaleString());

  } catch (e) {
    console.error("Failed to load metrics:", e);
    alert("Couldn't load baseline_metrics.json. If opening from disk, start a local server (see README).");
  }
}

load();

  async function loadCodeSnippets() {
  const res = await fetch("./fraud.py", { cache: "no-store" });
  const txt = await res.text();

  const grab = (re) => {
    const m = txt.match(re);
    return m ? m[0].trim() : "";
  };

  // 1) Regression (works already for you)
  const regression = grab(/LogisticRegression[\s\S]*?classification_report\([\s\S]*?\)\n/m);

  // 2) Exports (works already for you)
  const exportsBlock = grab(/joblib\.dump[\s\S]*?(baseline_metrics\.json|transactions_with_scores\.(parquet|csv))[\s\S]*?\n/m);

  // 3) Cleaning — try multiple strategies
  let cleaning =
    // a) Function named clean_data(...)
    grab(/def\s+clean_data[\s\S]*?(?=^def\s|\Z)/m)
    // b) Section header with "Cleaning"
    || grab(/^[ \t]*#.*Cleaning[\s\S]*?(?=^\s*#\s*[-=]{3,}|^def\s|\Z)/m)
    // c) Keyword window around drop_duplicates / RobustScaler
    || (function () {
      const i = txt.search(/drop_duplicates|RobustScaler|to_parquet/);
      if (i === -1) return "";
      const start = Math.max(0, i - 800);   // ~20–30 lines before
      const end   = Math.min(txt.length, i + 1200); // ~30–40 lines after
      return txt.slice(start, end).trim();
    })();

  if (!cleaning) cleaning = "Could not auto-detect cleaning block. Consider adding markers (see Option B).";

  // Paint to the UI
  document.getElementById("code-cleaning").textContent = cleaning || "—";
  document.getElementById("code-regression").textContent = regression || "—";
  document.getElementById("code-exports").textContent = exportsBlock || "—";
}

document.addEventListener("DOMContentLoaded", loadCodeSnippets);
