Pages.timetracking = {
  async render(container) {
    const [logs, employments, projects] = await Promise.all([
      Api.worklogs(), Api.employments(), Api.projects(),
    ]);

    const empMap = Object.fromEntries(employments.map((e) => [e.id, e.organization]));
    const projMap = Object.fromEntries(projects.map((p) => [p.id, p.name]));

    if (!logs.length) {
      container.innerHTML = `
        <div class="page-header"><h1 class="page-title">Time Tracking</h1></div>
        ${emptyState("No work log entries yet. Add some on the Daily Work Log page.")}`;
      return;
    }

    const rows = logs.map((l) => ({
      date: l.date,
      month: l.date.slice(0, 7),
      org: empMap[l.employment_id] || "",
      project: projMap[l.project_id] || "",
      category: l.category,
      hours: l.hours,
    }));

    const months = [...new Set(rows.map((r) => r.month))].sort().reverse();

    container.innerHTML = `
      <div class="page-header"><h1 class="page-title">Time Tracking</h1></div>
      <div class="form-row">
        <div class="field" style="max-width:220px">
          <label>Month</label>
          <select id="tt-month">
            <option value="all">All</option>
            ${months.map((m) => `<option value="${m}">${m}</option>`).join("")}
          </select>
        </div>
      </div>
      <div id="tt-body"></div>
    `;

    const select = container.querySelector("#tt-month");
    const body = container.querySelector("#tt-body");
    const draw = () => renderBody(body, rows, select.value);
    select.addEventListener("change", draw);
    draw();
  },
};

function sumBy(rows, keyFn) {
  const totals = new Map();
  for (const r of rows) {
    const key = keyFn(r);
    if (!key) continue;
    totals.set(key, (totals.get(key) || 0) + r.hours);
  }
  return [...totals.entries()].sort((a, b) => b[1] - a[1]);
}

function barChart(pairs) {
  if (!pairs.length) return emptyState("No data.");
  const max = Math.max(...pairs.map((p) => p[1]));
  return `
    <div class="entry-list">
      ${pairs.map(([label, value]) => `
        <div>
          <div style="display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:4px;">
            <span>${escapeHtml(label)}</span><span class="muted">${value.toFixed(1)}h</span>
          </div>
          <div style="background:var(--surface-alt);border-radius:6px;height:10px;overflow:hidden;">
            <div style="background:var(--accent);height:100%;width:${(value / max) * 100}%;"></div>
          </div>
        </div>`).join("")}
    </div>`;
}

function renderBody(el, allRows, monthFilter) {
  const rows = monthFilter === "all" ? allRows : allRows.filter((r) => r.month === monthFilter);
  const totalHours = rows.reduce((sum, r) => sum + r.hours, 0);

  const byCategory = sumBy(rows, (r) => r.category);
  const byOrg = sumBy(rows, (r) => r.org);
  const byProject = sumBy(rows, (r) => r.project);
  const byMonth = sumBy(allRows, (r) => r.month).sort((a, b) => a[0].localeCompare(b[0]));

  el.innerHTML = `
    <div class="grid cols-2 section-gap">
      <div class="stat-card"><div class="stat-label">Total Hours</div><div class="stat-value">${totalHours.toFixed(1)}</div></div>
      <div class="stat-card"><div class="stat-label">Entries</div><div class="stat-value">${rows.length}</div></div>
    </div>

    <div class="two-col section-gap">
      <div class="card">
        <h2 class="card-title">Hours by category</h2>
        ${barChart(byCategory)}
      </div>
      <div class="card">
        <h2 class="card-title">Hours by organization</h2>
        ${barChart(byOrg)}
      </div>
    </div>

    <div class="two-col section-gap">
      <div class="card">
        <h2 class="card-title">Hours by project</h2>
        ${barChart(byProject)}
      </div>
      <div class="card">
        <h2 class="card-title">Monthly trend</h2>
        ${barChart(byMonth)}
      </div>
    </div>

    <div class="card section-gap">
      <h2 class="card-title">Raw log</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Date</th><th>Org</th><th>Project</th><th>Category</th><th>Hours</th></tr></thead>
          <tbody>
            ${rows.sort((a, b) => b.date.localeCompare(a.date)).map((r) => `
              <tr>
                <td>${formatDate(r.date)}</td>
                <td>${escapeHtml(r.org || "—")}</td>
                <td>${escapeHtml(r.project || "—")}</td>
                <td><span class="badge gray">${escapeHtml(r.category)}</span></td>
                <td>${r.hours}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
    </div>
  `;
}
