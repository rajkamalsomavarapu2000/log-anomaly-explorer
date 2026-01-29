const $ = (id) => document.getElementById(id);

const healthPill = $("healthPill");
const fileInput = $("fileInput");
const btnParse = $("btnParse");
const btnAnalyze = $("btnAnalyze");
const btnSpikes = $("btnSpikes");
const summary = $("summary");
const levels = $("levels");
const preview = $("preview");
const rare = $("rare");
const spikes = $("spikes");

const rareLevelFilter = $("rareLevelFilter");
const rareLoggerFilter = $("rareLoggerFilter");
const rareSort = $("rareSort");

const spikeLevelFilter = $("spikeLevelFilter");
const spikeLoggerFilter = $("spikeLoggerFilter");
const spikeTimeFrom = $("spikeTimeFrom");
const spikeTimeTo = $("spikeTimeTo");
const spikeSort = $("spikeSort");

let rareData = [];
let spikeData = [];

async function checkHealth() {
  try {
    const r = await fetch("/health");
    const j = await r.json();
    if (j.ok) {
      healthPill.textContent = "API OK";
      healthPill.className = "pill ok";
    } else throw new Error("bad");
  } catch {
    healthPill.textContent = "API DOWN";
    healthPill.className = "pill bad";
  }
}

function getFile() {
  const f = fileInput.files && fileInput.files[0];
  if (!f) throw new Error("Please choose a log file first.");
  return f;
}

function renderTable(container, columns, rows) {
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");

  columns.forEach(c => {
    const th = document.createElement("th");
    th.textContent = c.replace(/_/g, " ");
    trh.appendChild(th);
  });

  thead.appendChild(trh);

  const tbody = document.createElement("tbody");
  rows.forEach(r => {
    const tr = document.createElement("tr");
    columns.forEach(c => {
      const td = document.createElement("td");
      let val = r[c] ?? "";

      if (c === "window_ts" && val) {
        val = new Date(val * 1000).toISOString();
      }


      td.textContent = val.toString();
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  table.appendChild(thead);
  table.appendChild(tbody);

  container.innerHTML = "";
  container.appendChild(table);
}

function updateRareTable() {
  let filtered = rareData.filter(item => {
    if (rareLevelFilter.value && !item.key.startsWith(rareLevelFilter.value.toUpperCase() + " |")) return false;
    if (rareLoggerFilter.value && !item.key.includes(" | " + rareLoggerFilter.value + " |")) return false;
    return true;
  });

  if (rareSort.value === "score") {
    filtered.sort((a, b) => b.score - a.score);
  } else {
    filtered.sort((a, b) => a.count - b.count);
  }

  renderTable(rare, ["count", "score", "key", "explanation", "example_message"], filtered);
}

function updateSpikeTable() {
  let filtered = spikeData.filter(item => {
    if (spikeLevelFilter.value && !item.key.startsWith(spikeLevelFilter.value.toUpperCase() + " |")) return false;
    if (spikeLoggerFilter.value && !item.key.includes(" | " + spikeLoggerFilter.value + " |")) return false;

    let from = spikeTimeFrom.value ? new Date(spikeTimeFrom.value).getTime() / 1000 : -Infinity;
    let to = spikeTimeTo.value ? new Date(spikeTimeTo.value).getTime() / 1000 : Infinity;
    if (item.window_ts < from || item.window_ts > to) return false;

    return true;
  });

  if (spikeSort.value === "score") {
    filtered.sort((a, b) => b.score - a.score);
  } else {
    filtered.sort((a, b) => a.count - b.count);
  }

  renderTable(spikes, ["count", "score", "key", "explanation", "window_ts", "example_message"], filtered);
}

btnParse.addEventListener("click", async () => {
  try {
    btnParse.disabled = true;
    const f = getFile();

    const fd = new FormData();
    fd.append("file", f);

    const r = await fetch("/api/parse", { method: "POST", body: fd });
    const j = await r.json();

    summary.textContent = `File: ${f.name}
Total lines: ${j.total_lines}
Parsed lines: ${j.parsed}`;

    const lines = Object.entries(j.level_counts || {})
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${k}: ${v}`)
      .join("\n");

    levels.textContent = lines || "—";
    renderTable(preview, ["line_no", "ts", "level", "logger", "message"], j.sample || []);
  } catch (e) {
    alert(e.message || "Parse failed.");
  } finally {
    btnParse.disabled = false;
  }
});

btnAnalyze.addEventListener("click", async () => {
  try {
    btnAnalyze.disabled = true;
    const f = getFile();

    const fd = new FormData();
    fd.append("file", f);

    const r = await fetch("/api/analyze?top_k=12", {
      method: "POST",
      body: fd
    });

    const j = await r.json();

    summary.textContent = `File: ${f.name}
Total lines: ${j.total_lines}
Unique patterns: ${j.unique_patterns}`;

    rareData = j.rare_patterns || [];
    updateRareTable();
  } catch (e) {
    alert(e.message || "Analyze failed.");
  } finally {
    btnAnalyze.disabled = false;
  }
});

btnSpikes.addEventListener("click", async () => {
  try {
    btnSpikes.disabled = true;
    const f = getFile();

    const fd = new FormData();
    fd.append("file", f);

    const r = await fetch("/api/spikes?window_size=60&top_k=12", {
      method: "POST",
      body: fd
    });

    const j = await r.json();

    summary.textContent = `File: ${f.name}
Total lines: ${j.total_lines}
Unique patterns: ${j.unique_patterns}`;

    spikeData = j.spike_patterns || [];
    updateSpikeTable();
  } catch (e) {
    alert(e.message || "Spike detection failed.");
  } finally {
    btnSpikes.disabled = false;
  }
});



rareSort.addEventListener("change", updateRareTable);
rareLevelFilter.addEventListener("input", updateRareTable);
rareLoggerFilter.addEventListener("input", updateRareTable);

spikeSort.addEventListener("change", updateSpikeTable);
spikeLevelFilter.addEventListener("input", updateSpikeTable);
spikeLoggerFilter.addEventListener("input", updateSpikeTable);
spikeTimeFrom.addEventListener("change", updateSpikeTable);
spikeTimeTo.addEventListener("change", updateSpikeTable);

checkHealth();
