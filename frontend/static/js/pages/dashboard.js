Pages.dashboard = {
  async render(container) {
    const data = await Api.dashboard();

    const stat = (label, value) => `
      <div class="stat-card">
        <div class="stat-label">${escapeHtml(label)}</div>
        <div class="stat-value">${escapeHtml(value)}</div>
      </div>`;

    const projectsHtml = data.current_projects.length
      ? data.current_projects.map((p) => `
          <div class="entry-item">
            <div class="entry-item-head">
              <span class="entry-item-title">${escapeHtml(p.name)}</span>
              <span class="badge blue">${escapeHtml(p.status)}</span>
            </div>
            <div class="entry-item-body">${escapeHtml(p.organization || "—")}</div>
          </div>`).join("")
      : emptyState("No active projects yet. Add one on the Projects page.");

    const achievementsHtml = data.recent_achievements.length
      ? data.recent_achievements.map((a) => `
          <div class="entry-item">
            <div class="entry-item-head">
              <span class="entry-item-title">✓ ${escapeHtml(a.title)}</span>
            </div>
            <div class="entry-item-body">${escapeHtml(a.category || "")}</div>
          </div>`).join("")
      : emptyState("No achievements logged yet. Add one on the Achievements page.");

    const logsRows = data.recent_logs.length
      ? data.recent_logs.map((l) => `
          <tr>
            <td>${formatDate(l.date)}</td>
            <td>${l.hours}</td>
            <td><span class="badge gray">${escapeHtml(l.category)}</span></td>
            <td>${escapeHtml(l.raw_text.slice(0, 90))}${l.raw_text.length > 90 ? "…" : ""}</td>
          </tr>`).join("")
      : `<tr><td colspan="4">${emptyState("No work log entries yet. Start on Daily Work Log.")}</td></tr>`;

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Professional Life Dashboard</h1>
          <div class="page-subtitle">Your career command center.</div>
        </div>
      </div>

      <div class="grid cols-5">
        ${stat("Hours This Month", data.hours_month.toFixed(1))}
        ${stat("Hours This Year", data.hours_year.toFixed(1))}
        ${stat("Active Projects", data.active_projects)}
        ${stat("Achievements This Month", data.accomplishments_month)}
        ${stat("Skills Tracked", data.skills_count)}
      </div>

      <div class="two-col section-gap">
        <div class="card">
          <h2 class="card-title">Current Projects</h2>
          <div class="entry-list">${projectsHtml}</div>
        </div>
        <div class="card">
          <h2 class="card-title">Recent Accomplishments</h2>
          <div class="entry-list">${achievementsHtml}</div>
        </div>
      </div>

      <div class="card section-gap">
        <h2 class="card-title">Recent Work Log Entries</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Date</th><th>Hours</th><th>Category</th><th>Summary</th></tr></thead>
            <tbody>${logsRows}</tbody>
          </table>
        </div>
      </div>
    `;
  },
};
