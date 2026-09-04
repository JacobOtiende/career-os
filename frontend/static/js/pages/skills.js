Pages.skills = {
  async render(container) {
    const skills = await Api.skills();

    if (!skills.length) {
      container.innerHTML = `
        <div class="page-header"><h1 class="page-title">Skills &amp; Competency Graph</h1></div>
        ${emptyState("No skills tracked yet. They accumulate automatically as you log work, projects, and achievements.")}`;
      return;
    }

    const categories = [...new Set(skills.map((s) => s.category))].sort();

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Skills &amp; Competency Graph</h1>
          <div class="page-subtitle">Not just a level — every skill is backed by linked evidence.</div>
        </div>
      </div>

      <div class="field" style="max-width:320px">
        <label>Category</label>
        <div>
          ${categories.map((c) => `<label class="small" style="margin-right:14px;"><input type="checkbox" class="cat-filter" value="${c}" checked /> ${c}</label>`).join("")}
        </div>
      </div>

      <div class="card section-gap">
        <div class="table-wrap"><table>
          <thead><tr><th>Skill</th><th>Category</th><th>Evidence Count</th><th>Last Demonstrated</th></tr></thead>
          <tbody id="skills-tbody"></tbody>
        </table></div>
      </div>

      <div class="card section-gap">
        <h2 class="card-title">Evidence detail</h2>
        <div class="field" style="max-width:320px">
          <label>Select a skill to see evidence</label>
          <select id="skill-select"></select>
        </div>
        <div id="evidence-detail"></div>
      </div>
    `;

    const tbody = container.querySelector("#skills-tbody");
    const skillSelect = container.querySelector("#skill-select");
    const evidenceEl = container.querySelector("#evidence-detail");
    const checkboxes = [...container.querySelectorAll(".cat-filter")];

    async function loadEvidence(skillId) {
      const evidence = await Api.skillEvidence(skillId);
      const labelMap = { work_log: "Work Log", project: "Project", achievement: "Achievement" };
      evidenceEl.innerHTML = evidence.length
        ? `<div class="entry-list section-gap">${evidence.map((e) => `
            <div class="entry-item">
              <div class="entry-item-head">
                <span class="entry-item-title">${labelMap[e.source_type] || e.source_type} #${e.source_id}</span>
                <span class="entry-item-meta">${formatDate(e.demonstrated_on)}</span>
              </div>
              <div class="entry-item-body">${escapeHtml(e.note)}</div>
            </div>`).join("")}</div>`
        : emptyState("No evidence recorded for this skill.");
    }

    function draw() {
      const activeCats = new Set(checkboxes.filter((c) => c.checked).map((c) => c.value));
      const filtered = skills.filter((s) => activeCats.has(s.category))
        .sort((a, b) => b.evidence_count - a.evidence_count);

      tbody.innerHTML = filtered.map((s) => `
        <tr>
          <td>${escapeHtml(s.name)}</td>
          <td><span class="badge gray">${escapeHtml(s.category)}</span></td>
          <td>${s.evidence_count}</td>
          <td>${s.last_demonstrated ? formatDate(s.last_demonstrated) : "—"}</td>
        </tr>`).join("");

      const prev = skillSelect.value;
      skillSelect.innerHTML = filtered.map((s) => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join("");
      if (filtered.some((s) => String(s.id) === prev)) skillSelect.value = prev;
      if (filtered.length) loadEvidence(skillSelect.value);
      else evidenceEl.innerHTML = "";
    }

    checkboxes.forEach((cb) => cb.addEventListener("change", draw));
    skillSelect.addEventListener("change", () => loadEvidence(skillSelect.value));
    draw();
  },
};
