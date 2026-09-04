Pages.jobs = {
  async render(container) {
    const jds = await Api.jobs();

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Job Description Analyzer &amp; Match Engine</h1>
        </div>
      </div>

      <div class="card">
        <h2 class="card-title">Paste a target job description</h2>
        <div class="form-row">
          <div class="field"><label>Job title</label><input type="text" id="jd-title" /></div>
          <div class="field"><label>Company</label><input type="text" id="jd-company" /></div>
        </div>
        <div class="field"><label>Job description text</label><textarea id="jd-text" rows="8"></textarea></div>
        <div class="btn-row"><button id="jd-analyze-btn" class="btn-primary" disabled>Analyze</button></div>
      </div>

      <div class="card section-gap">
        <div class="field" style="max-width:420px">
          <label>Select a job description to view its match</label>
          <select id="jd-select">${jds.map((j) => `<option value="${j.id}">${escapeHtml(j.title || "Untitled")} — ${escapeHtml(j.company)} (#${j.id})</option>`).join("")}</select>
        </div>
        <div id="jd-detail"></div>
      </div>
    `;

    const textArea = container.querySelector("#jd-text");
    const analyzeBtn = container.querySelector("#jd-analyze-btn");
    textArea.addEventListener("input", () => { analyzeBtn.disabled = !textArea.value.trim(); });

    analyzeBtn.addEventListener("click", () =>
      withBusy(analyzeBtn, async () => {
        try {
          const jd = await Api.createJob({
            title: container.querySelector("#jd-title").value,
            company: container.querySelector("#jd-company").value,
            raw_text: textArea.value,
          });
          toast("Analyzed.");
          Router.navigate();
        } catch (err) {
          toast(`Analysis failed: ${err.message}`, true);
        }
      })
    );

    const select = container.querySelector("#jd-select");
    const detail = container.querySelector("#jd-detail");
    if (!jds.length) {
      detail.innerHTML = emptyState("No job descriptions analyzed yet.");
      return;
    }
    select.addEventListener("change", () => loadDetail(detail, select.value));
    loadDetail(detail, select.value);
  },
};

async function loadDetail(el, jobId) {
  el.innerHTML = emptyState("Loading…");
  const jd = await Api.getJob(jobId);
  const m = jd.match;

  const matchList = (label, items, cls) => `
    <div>
      <div class="small" style="font-weight:600;margin-bottom:6px;">${label}</div>
      ${items.length ? `<div class="tag-list">${items.map((s) => `<span class="badge ${cls}">${escapeHtml(s)}</span>`).join("")}</div>` : `<span class="muted small">none</span>`}
    </div>`;

  el.innerHTML = `
    <div class="section-gap">
      <div class="small"><strong>Required skills found:</strong> ${jd.required_skills || "—"}</div>
      <div class="small"><strong>Preferred skills found:</strong> ${jd.preferred_skills || "—"}</div>
      <div class="small"><strong>Competencies found:</strong> ${jd.competencies || "—"}</div>
    </div>

    <div class="grid cols-3 section-gap">
      <div class="stat-card"><div class="stat-label">Overall Match</div><div class="stat-value">${m.overall_pct}%</div></div>
      <div class="stat-card"><div class="stat-label">Required Skills Match</div><div class="stat-value">${m.required_pct}%</div></div>
      <div class="stat-card"><div class="stat-label">Preferred Skills Match</div><div class="stat-value">${m.preferred_pct}%</div></div>
    </div>

    <div class="grid cols-3 section-gap">
      ${matchList("✓ Strong Matches", m.strong_matches, "green")}
      ${matchList("△ Partial Matches", m.partial_matches, "amber")}
      ${matchList("! Gaps", m.gaps, "red")}
    </div>

    <div class="card section-gap">
      <h2 class="card-title">Recommended evidence</h2>
      ${jd.recommended_evidence.length
        ? `<div class="entry-list">${jd.recommended_evidence.map((r) => `
            <div class="entry-item"><span class="entry-item-title">${escapeHtml(r.title)}</span>
            <span class="entry-item-meta">${r.overlap} matching skill${r.overlap !== 1 ? "s" : ""}</span></div>`).join("")}</div>`
        : emptyState("No achievements overlap with this job's skills yet.")}
    </div>
    <div class="small muted section-gap">Generate a targeted resume from this analysis on the Resume Generator page.</div>
  `;
}
