Pages.export = {
  async render(container) {
    const tables = await Api.exportTables();

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Data Export</h1>
          <div class="page-subtitle">This database is meant to become years of career evidence — back it up regularly.</div>
        </div>
      </div>

      <div class="card">
        <h2 class="card-title">Export a table as CSV</h2>
        <div class="field" style="max-width:280px">
          <label>Table</label>
          <select id="table-select">${tables.map((t) => `<option value="${t}">${t}</option>`).join("")}</select>
        </div>
        <div class="btn-row">
          <a id="csv-link" class="btn-secondary" style="text-decoration:none;display:inline-block;" href="#">⬇️ Download CSV</a>
        </div>
        <div class="table-wrap section-gap" id="table-preview"></div>
      </div>

      <div class="card section-gap">
        <h2 class="card-title">Export everything as JSON</h2>
        <button id="json-export-btn" class="btn-primary">⬇️ Download full export</button>
      </div>
    `;

    const select = container.querySelector("#table-select");
    const csvLink = container.querySelector("#csv-link");
    const preview = container.querySelector("#table-preview");

    async function loadPreview() {
      const table = select.value;
      csvLink.href = `/api/export/table/${table}/csv`;
      const rows = await Api.exportTable(table);
      if (!rows.length) {
        preview.innerHTML = emptyState("Table is empty.");
        return;
      }
      const cols = Object.keys(rows[0]);
      preview.innerHTML = `
        <table>
          <thead><tr>${cols.map((c) => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead>
          <tbody>
            ${rows.slice(0, 100).map((r) => `<tr>${cols.map((c) => `<td>${escapeHtml(r[c])}</td>`).join("")}</tr>`).join("")}
          </tbody>
        </table>`;
    }

    select.addEventListener("change", loadPreview);
    loadPreview();

    container.querySelector("#json-export-btn").addEventListener("click", async (e) => {
      await withBusy(e.target, async () => {
        const res = await fetch("/api/export/all");
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "career_os_export.json";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      });
    });
  },
};
