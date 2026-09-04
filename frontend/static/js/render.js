const Pages = {};

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  if (isNaN(d)) return iso;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function csvSplit(str) {
  return (str || "").split(",").map((s) => s.trim()).filter(Boolean);
}

function tagList(items) {
  const list = Array.isArray(items) ? items : csvSplit(items);
  if (!list.length) return `<span class="muted small">none</span>`;
  return `<div class="tag-list">${list.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("")}</div>`;
}

function toast(message, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.className = "toast" + (isError ? " error" : ""); }, 3200);
}

function emptyState(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

async function withBusy(button, fn) {
  const original = button.innerHTML;
  button.disabled = true;
  button.innerHTML = `<span class="spinner"></span>${original}`;
  try {
    return await fn();
  } finally {
    button.disabled = false;
    button.innerHTML = original;
  }
}

function optionsHtml(items, valueKey, labelKey, selectedValue) {
  const opts = [`<option value="">— none —</option>`];
  for (const item of items) {
    const v = item[valueKey];
    const selected = String(v) === String(selectedValue) ? "selected" : "";
    opts.push(`<option value="${escapeHtml(v)}" ${selected}>${escapeHtml(item[labelKey])}</option>`);
  }
  return opts.join("");
}
