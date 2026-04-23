// ── STATE ──────────────────────────────────────────────────
const state = { snapshot: null };

const r2rTimeline = [
  { key: "je",          title: "Journal Entry Posting",    code: "FB50"     },
  { key: "accrual",     title: "Accruals and Provisions",  code: "FBS1"     },
  { key: "depreciation",title: "Depreciation Run",         code: "AFAB"     },
  { key: "recon",       title: "GL Reconciliation",        code: "FAGLF03"  },
  { key: "adj",         title: "Adjustment Entries",       code: "F-02"     },
  { key: "tb",          title: "Trial Balance",            code: "F.08"     },
  { key: "close",       title: "Period / Year-End Close",  code: "OB52"     },
  { key: "report",      title: "Financial Statements",     code: "F.01"     },
];

// ── HELPERS ────────────────────────────────────────────────
function inr(value) {
  const n = Number(value || 0);
  return "₹" + new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(Math.round(n));
}

function fmt(value) {
  if (!value) return "—";
  try { return new Date(value).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }); }
  catch { return value; }
}

function setBanner(msg, type = "neutral") {
  const el = document.getElementById("systemBanner");
  el.textContent = msg;
  el.className = `system-banner ${type}`;
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : null;
  if (!res.ok) throw new Error(data?.error || `Request failed: ${res.status}`);
  return data;
}

function formToObj(form) {
  const d = Object.fromEntries(new FormData(form).entries());
  Object.keys(d).forEach(k => { if (d[k] === "") delete d[k]; });
  return d;
}

function typeLabel(t) {
  const map = { je: "Journal Entry", accrual: "Accrual", depreciation: "Depreciation", adj: "Adjustment" };
  return map[t] || t.toUpperCase();
}

function typePill(t) {
  const map = { je: "info", accrual: "purple", depreciation: "warning", adj: "neutral" };
  return `<span class="pill ${map[t] || 'neutral'}">${typeLabel(t)}</span>`;
}

// ── POPULATE GL SELECTS ────────────────────────────────────
function populateGLSelects() {
  if (!state.snapshot) return;
  const accounts = state.snapshot.glAccounts || {};
  const options = Object.entries(accounts)
    .map(([code, name]) => `<option value="${code}">${code} — ${name}</option>`)
    .join("");

  const ids = [
    "je-debit-select", "je-credit-select",
    "accrual-debit-select", "accrual-credit-select",
    "adj-debit-select", "adj-credit-select",
  ];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = options;
  });

  // cost centres
  const ccs = state.snapshot.costCenters || {};
  const ccOpts = Object.entries(ccs)
    .map(([code, name]) => `<option value="${code}">${code} — ${name}</option>`)
    .join("");
  ["je-cc-select","accrual-cc-select","dep-cc-select","adj-cc-select"]
    .forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = ccOpts; });
}

// ── RENDER TIMELINE ────────────────────────────────────────
function renderTimeline() {
  const pd = state.snapshot.processData;
  const container = document.getElementById("timeline");
  const tpl = document.getElementById("tlItemTpl");
  container.innerHTML = "";
  let done = 0;

  r2rTimeline.forEach((step, i) => {
    const node = tpl.content.firstElementChild.cloneNode(true);
    const doc = pd[step.key];
    const marker = node.querySelector(".tl-marker");
    const titleEl = node.querySelector(".tl-title");
    const codeEl = node.querySelector(".tl-code");
    const statusEl = node.querySelector(".tl-status");
    const metaEl = node.querySelector(".tl-meta");

    titleEl.textContent = step.title;
    codeEl.textContent = step.code;
    marker.textContent = i + 1;

    if (doc) {
      done++;
      marker.classList.add("done");
      marker.textContent = "✓";
      statusEl.textContent = "Completed";
      statusEl.className = "pill success tl-status";
      metaEl.textContent = doc.number
        ? `${doc.number} · ${fmt(doc.createdOn)}${doc.description ? " · " + doc.description : ""}`
        : "Completed";
    } else {
      statusEl.textContent = "Pending";
      statusEl.className = "pill neutral tl-status";
      metaEl.textContent = "Not executed yet.";
    }
    container.appendChild(node);
  });

  const pct = Math.round((done / r2rTimeline.length) * 100);
  document.getElementById("progressFill").style.width = pct + "%";
  document.getElementById("progressPct").textContent = pct + "% complete";
  document.getElementById("overviewReconPill").textContent = `${done} / ${r2rTimeline.length} steps`;
  document.getElementById("overviewReconPill").className = done === r2rTimeline.length ? "pill success" : "pill neutral";
}

// ── RENDER OVERVIEW ────────────────────────────────────────
function renderOverview() {
  const m = state.snapshot.metrics;
  const fs = state.snapshot.financialStatements;
  const tb = state.snapshot.trialBalance;

  document.getElementById("metricJE").textContent = m.totalPostings;
  document.getElementById("metricDebits").textContent = inr(m.totalDebits);
  document.getElementById("metricPAT").textContent = inr(m.netIncome);
  document.getElementById("metricPeriod").textContent = m.periodClosed ? "Closed" : "Open";
  document.getElementById("sumRevenue").textContent = inr(fs.pnl.revenue);
  document.getElementById("sumPAT").textContent = inr(fs.pnl.pat);

  if (m.totalPostings === 0) {
    document.getElementById("sumTBStatus").textContent = "No data";
    document.getElementById("overviewMatchPill").textContent = "No entries posted yet";
    document.getElementById("overviewMatchPill").className = "pill neutral";
  } else if (tb.balanced) {
    document.getElementById("sumTBStatus").textContent = "Balanced ✓";
    document.getElementById("overviewMatchPill").textContent = "Trial Balance — Balanced";
    document.getElementById("overviewMatchPill").className = "pill success";
  } else {
    document.getElementById("sumTBStatus").textContent = "Unbalanced!";
    document.getElementById("overviewMatchPill").textContent = "Trial Balance — UNBALANCED";
    document.getElementById("overviewMatchPill").className = "pill danger";
  }
}

// ── RENDER MASTER DATA ─────────────────────────────────────
function renderMasterData() {
  const md = state.snapshot.masterData;

  const orgGrid = document.getElementById("orgDataGrid");
  orgGrid.innerHTML = (md.organization || []).map(([l, v]) =>
    `<div class="data-card"><div class="dc-lbl">${l}</div><div class="dc-val">${v}</div></div>`
  ).join("");

  const glList = document.getElementById("glAccountList");
  glList.innerHTML = (md.glAccounts || []).map(([code, name]) =>
    `<div class="gl-row"><span class="gl-code">${code}</span><span class="gl-name">${name}</span></div>`
  ).join("");

  const ccGrid = document.getElementById("costCenterGrid");
  ccGrid.innerHTML = (md.costCenters || []).map(([code, name]) =>
    `<div class="data-card"><div class="dc-lbl">${code}</div><div class="dc-val">${name}</div></div>`
  ).join("");
}

// ── RENDER JE LEDGER ───────────────────────────────────────
function renderJELedger() {
  const entries = state.snapshot.journalEntries || [];
  const body = document.getElementById("jeLedgerBody");
  const accounts = state.snapshot.glAccounts || {};
  document.getElementById("jeLedgerCount").textContent = `${entries.length} entries`;
  document.getElementById("jeLedgerCount").className = entries.length ? "pill success" : "pill neutral";

  if (!entries.length) {
    body.innerHTML = `<tr><td colspan="9" style="text-align:center;color:var(--text-muted);padding:24px;">No journal entries posted yet. Use the forms above to post entries.</td></tr>`;
    return;
  }

  body.innerHTML = entries.map(e => `
    <tr>
      <td class="mono">${e.jeNumber}</td>
      <td>${typePill(e.entryType)}</td>
      <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${e.description}">${e.description}</td>
      <td><span class="mono">${e.debitAccount}</span><br><span style="font-size:11px;color:var(--text-muted);">${accounts[e.debitAccount] || ""}</span></td>
      <td><span class="mono">${e.creditAccount}</span><br><span style="font-size:11px;color:var(--text-muted);">${accounts[e.creditAccount] || ""}</span></td>
      <td class="td-amount">${inr(e.amount)}</td>
      <td>${e.costCenter}</td>
      <td>${fmt(e.postingDate)}</td>
      <td><span class="pill success">${e.status}</span></td>
    </tr>
  `).join("");
}

// ── RENDER TRIAL BALANCE ───────────────────────────────────
function renderTrialBalance() {
  const tb = state.snapshot.trialBalance;
  const body = document.getElementById("tbBody");

  const badge = document.getElementById("tbBalancedBadge");
  if (tb.rows.length > 0) {
    badge.style.display = "inline-flex";
    if (tb.balanced) {
      badge.className = "tb-balanced-badge ok";
      badge.textContent = "✓ Balanced — Dr = Cr";
    } else {
      badge.className = "tb-balanced-badge error";
      badge.textContent = "✗ Unbalanced — Variance Detected";
    }
  } else {
    badge.style.display = "none";
  }

  document.getElementById("tbTotalDebit").textContent = inr(tb.totalDebit);
  document.getElementById("tbTotalCredit").textContent = inr(tb.totalCredit);

  if (!tb.rows.length) {
    body.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:24px;">No entries posted. Post journal entries to generate trial balance.</td></tr>`;
    return;
  }

  body.innerHTML = tb.rows.map(r => {
    const net = r.debit - r.credit;
    const netStr = net >= 0 ? `<span class="fs-positive">${inr(net)}</span>` : `<span class="fs-negative">${inr(Math.abs(net))}</span>`;
    return `
      <tr>
        <td class="mono">${r.account}</td>
        <td>${r.name}</td>
        <td class="td-amount">${inr(r.debit)}</td>
        <td class="td-amount">${inr(r.credit)}</td>
        <td class="td-amount">${netStr}</td>
      </tr>
    `;
  }).join("");

  // Reconciliation checklist
  const recon = state.snapshot.reconciliation;
  const reconEl = document.getElementById("reconChecklist");
  reconEl.innerHTML = recon.items.map((item, i) => `
    <div class="recon-item">
      <div class="recon-icon ${item.status}">
        ${item.status === "done" ? "✓" : item.status === "error" ? "✗" : "○"}
      </div>
      <div>
        <div class="recon-label">${item.label}</div>
        <div class="recon-detail">${item.detail}</div>
      </div>
      <span class="recon-step-num">Step ${i + 1}</span>
    </div>
  `).join("");

  // TB Alerts
  const alertsEl = document.getElementById("tbAlerts");
  const alerts = [];
  if (!tb.balanced && tb.rows.length > 0) {
    alerts.push({ type: "danger", title: "Trial Balance Unbalanced", body: `Debit total ${inr(tb.totalDebit)} ≠ Credit total ${inr(tb.totalCredit)}. Review journal entries for missing entries.` });
  }
  if (tb.balanced && tb.rows.length > 0) {
    alerts.push({ type: "success", title: "Trial Balance Balanced", body: `All debits equal credits. Total: ${inr(tb.totalDebit)}. Ready for financial statement generation.` });
  }
  if (!state.snapshot.journalEntries.some(e => e.entryType === "accrual")) {
    alerts.push({ type: "warning", title: "Accruals Not Posted", body: "No FBS1 accrual entries found. Month-end accruals should be posted before period close." });
  }
  if (!state.snapshot.journalEntries.some(e => e.entryType === "depreciation")) {
    alerts.push({ type: "warning", title: "Depreciation Not Run", body: "AFAB depreciation run has not been executed for this period." });
  }
  if (!alerts.length) {
    alertsEl.innerHTML = `<div class="alert-card success"><h4>No Exceptions</h4><p>All reconciliation checks passed. Process is in order.</p></div>`;
  } else {
    alertsEl.innerHTML = alerts.map(a => `<div class="alert-card ${a.type}"><h4>${a.title}</h4><p>${a.body}</p></div>`).join("");
  }
}

// ── RENDER FINANCIAL STATEMENTS ────────────────────────────
function renderFinancialStatements() {
  const fs = state.snapshot.financialStatements;
  const pnl = fs.pnl;
  const bs = fs.balanceSheet;

  const set = (id, val, forceNeg = false) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = inr(Math.abs(val));
    if (val < 0 || forceNeg) el.className = "fs-negative";
    else if (val > 0) el.className = "fs-positive";
    else el.className = "fs-neutral";
  };

  set("fs-revenue", pnl.revenue);
  document.getElementById("fs-otherincome").textContent = inr(0);
  set("fs-totalrev", pnl.revenue);
  set("fs-cogs", pnl.cogs, true);
  set("fs-gp", pnl.grossProfit);
  set("fs-salaries", pnl.opex, true);
  document.getElementById("fs-dep").textContent = "—";
  document.getElementById("fs-admin").textContent = "—";
  set("fs-ebit", pnl.ebit);
  set("fs-finance", pnl.financeCosts, true);
  set("fs-pbt", pnl.pbt);
  set("fs-tax", pnl.tax, true);
  set("fs-pat", pnl.pat);

  document.getElementById("bs-assets").textContent = inr(bs.totalAssets);
  document.getElementById("bs-liabilities").textContent = inr(bs.totalLiabilities);
  document.getElementById("bs-equity").textContent = inr(bs.totalEquity);
  const bsCheck = document.getElementById("bs-check");
  if (bs.balanced && bs.totalAssets > 0) {
    bsCheck.textContent = "Balanced ✓";
    bsCheck.className = "pill success";
  } else if (bs.totalAssets > 0) {
    bsCheck.textContent = "Unbalanced ✗";
    bsCheck.className = "pill danger";
  } else {
    bsCheck.textContent = "Pending";
    bsCheck.className = "pill neutral";
  }
}

// ── RENDER PERIOD CLOSE ────────────────────────────────────
function renderPeriodClose() {
  const closes = state.snapshot.periodCloses || [];
  const histEl = document.getElementById("closeHistory");
  const checkEl = document.getElementById("closeChecklist");

  if (!closes.length) {
    histEl.innerHTML = `<div class="empty-state"><div class="es-icon">🔒</div><p>No period closes executed yet. Use the Transactions tab to execute OB52.</p></div>`;
  } else {
    histEl.innerHTML = closes.map(c => `
      <div style="background:var(--sap-green-bg);border:1px solid rgba(16,126,62,0.2);border-radius:var(--radius-lg);padding:14px;margin-bottom:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <span class="mono" style="font-weight:600;">${c.closeNumber}</span>
          <span class="pill success">${c.status}</span>
        </div>
        <div style="font-size:13px;color:var(--text-muted);margin-bottom:8px;">
          ${c.closeType === "year-end" ? "Year-End Close" : "Month-End Close"} · ${c.period} · FY${c.fiscalYear} · by ${c.closedBy}
        </div>
        ${c.steps.map(s => `
          <div class="close-step">
            <div class="close-check ${s.status === "Completed" ? "done" : "na"}">${s.status === "Completed" ? "✓" : "—"}</div>
            <span class="close-step-label">${s.step}</span>
          </div>
        `).join("")}
      </div>
    `).join("");
  }

  // Standard checklist
  const standardSteps = [
    "Verify all journals posted (FB50)",
    "Run depreciation (AFAB)",
    "Post accruals and provisions (FBS1)",
    "Review intercompany transactions",
    "GL reconciliation and clearing (FAGLF03)",
    "Trial balance review (F.08)",
    "Post adjustment entries (F-02)",
    "Generate financial statements (F.01)",
    "Management review and approval",
    "Close posting period (OB52)",
  ];
  const recon = state.snapshot.reconciliation;
  checkEl.innerHTML = standardSteps.map((step, i) => {
    const done = i < recon.completed;
    return `
      <div class="close-step">
        <div class="close-check ${done ? "done" : "na"}">${done ? "✓" : String(i + 1)}</div>
        <span class="close-step-label" style="${done ? "color:var(--text-muted);text-decoration:line-through;" : ""}">${step}</span>
      </div>
    `;
  }).join("");
}

// ── RENDER ALL ─────────────────────────────────────────────
function renderAll() {
  populateGLSelects();
  renderOverview();
  renderTimeline();
  renderMasterData();
  renderJELedger();
  renderTrialBalance();
  renderFinancialStatements();
  renderPeriodClose();
}

// ── NAVIGATION ─────────────────────────────────────────────
function activateSection(id) {
  document.querySelectorAll(".section").forEach(s => s.classList.toggle("active", s.id === id));
  document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.section === id));
  document.querySelectorAll(".shell-nav-item").forEach(b => b.classList.toggle("active", b.dataset.section === id));
}

function activateTxn(id) {
  document.querySelectorAll(".txn-tab").forEach(b => b.classList.toggle("active", b.dataset.txn === id));
  document.querySelectorAll(".txn-form").forEach(f => f.classList.toggle("active", f.id === `form-${id}`));
}

// ── API ACTIONS ────────────────────────────────────────────
async function refreshState(msg = "System synchronised.") {
  state.snapshot = await api("/api/state");
  renderAll();
  setBanner(msg, "success");
}

async function submitTxn(type, form) {
  setBanner(`Posting ${type.toUpperCase()} transaction…`, "neutral");
  try {
    const snap = await api(`/api/transactions/${type}`, { method: "POST", body: JSON.stringify(formToObj(form)) });
    state.snapshot = snap;
    renderAll();
    form.reset();
    setBanner(`${type.toUpperCase()} transaction posted successfully.`, "success");
  } catch (err) {
    setBanner(err.message, "danger");
  }
}

async function loadDemo() {
  setBanner("Loading demo data…", "neutral");
  try {
    state.snapshot = await api("/api/seed", { method: "POST", body: "{}" });
    renderAll();
    setBanner("Demo data loaded — full R2R cycle populated.", "success");
  } catch (err) { setBanner(err.message, "danger"); }
}

async function resetAll() {
  if (!confirm("Reset all transactional data? This cannot be undone.")) return;
  setBanner("Resetting…", "neutral");
  try {
    state.snapshot = await api("/api/reset", { method: "POST", body: "{}" });
    renderAll();
    setBanner("All data reset.", "warning");
  } catch (err) { setBanner(err.message, "danger"); }
}

async function exportSnap() {
  try {
    const data = await api("/api/export");
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "buildright-r2r-snapshot.json";
    a.click();
    URL.revokeObjectURL(a.href);
    setBanner("Snapshot exported.", "success");
  } catch (err) { setBanner(err.message, "danger"); }
}

// ── BIND EVENTS ────────────────────────────────────────────
function bindEvents() {
  document.querySelectorAll(".nav-item, .shell-nav-item").forEach(b => {
    b.addEventListener("click", () => activateSection(b.dataset.section));
  });
  document.querySelectorAll(".txn-tab").forEach(b => {
    b.addEventListener("click", () => activateTxn(b.dataset.txn));
  });

  ["je","accrual","depreciation","adj","close"].forEach(type => {
    const form = document.getElementById(`form-${type}`);
    if (form) form.addEventListener("submit", e => { e.preventDefault(); submitTxn(type, form); });
  });

  document.getElementById("seedBtn").addEventListener("click", loadDemo);
  document.getElementById("resetBtn").addEventListener("click", resetAll);
  document.getElementById("exportBtn").addEventListener("click", exportSnap);
}

// ── BOOTSTRAP ──────────────────────────────────────────────
async function bootstrap() {
  bindEvents();
  setBanner("Connecting to backend…", "neutral");
  try {
    await refreshState("Backend connected. BuildRight R2R Command Center ready.");
  } catch (err) {
    setBanner("Cannot connect to backend. Start app.py first: python app.py", "danger");
  }
}

bootstrap();
