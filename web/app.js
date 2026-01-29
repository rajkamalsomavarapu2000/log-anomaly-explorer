const $ = (id) => document.getElementById(id);

const healthPill = $("healthPill");
const fileInput = $("fileInput");
const btnParse = $("btnParse");
const btnAnalyze = $("btnAnalyze");
const summary = $("summary");
const levels = $("levels");
const preview = $("preview");
const rare = $("rare");

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
    th.textContent = c;
    trh.appendChild(th);
  });
  thead.appendChild(trh);

  const tbody = document.createElement("tbody");
  rows.forEach(r => {
    const tr = document.createElement("tr");
    columns.forEach(c => {
      const td = document.createElement("td");
      td.textContent = (r[c] ?? "").toString();
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  table.appendChild(thead);
  table.appendChild(tbody);

  container.innerHTML = "";
  container.appendChild(table);
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

    // Level counts
    const lines = Object.entries(j.level_counts || {})
      .sort((a,b) => b[1] - a[1])
      .map(([k,v]) => `${k}: ${v}`)
      .join("\n");
    levels.textContent = lines || "—";

    // Preview table
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

    const r = await fetch("/api/analyze?top_k=12", { method: "POST", body: fd });
    const j = await r.json();

    summary.textContent = `File: ${f.name}
Total lines: ${j.total_lines}
Unique patterns: ${j.unique_patterns}`;

    renderTable(rare, ["count", "key", "example_message"], j.rare_patterns || []);
  } catch (e) {
    alert(e.message || "Analyze failed.");
  } finally {
    btnAnalyze.disabled = false;
  }
});

checkHealth();
