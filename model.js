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
