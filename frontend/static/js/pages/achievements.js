Pages.achievements = {
  async render(container) {
    const [achievements, worklogs, projects, status] = await Promise.all([
      Api.achievements(), Api.worklogs(), Api.projects(), Api.status(),
    ]);

    const categories = ["Leadership", "Technical", "Analytics", "Process Improvement", "Other"];

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Achievement / Impact Tracker</h1>
          <div class="page-subtitle">"What changed because of your work?" — Situation / Task / Action / Result / Metric.</div>
        </div>
      </div>

      <details class="expandable">
        <summary>Add an achievement</summary>
        <div class="section-gap">
          ${status.llm_available ? `
            <div class="form-row">
              <div class="field" style="flex:3">
                <label>Draft from a work log entry (optional)</label>
                <select id="a-source-log">
                  <option value="">— start from scratch —</option>
                  ${worklogs.slice(0, 100).map((l) => `<option value="${l.id}">${escapeHtml(l.date)} — ${escapeHtml(l.raw_text.slice(0, 60))}</option>`).join("")}
                </select>
              </div>
              <div class="field" style="flex:1;display:flex;align-items:flex-end;">
                <button id="a-draft-btn" class="btn-secondary" type="button">🤖 Draft STAR from this entry</button>
              </div>
            </div>
          ` : `<div class="small muted">AI drafting is off (no API key set). Fill in the fields manually below.</div>`}

          <form id="achievement-form" class="section-gap">
            <div class="field"><label>Achievement title*</label><input type="text" id="a-title" required /></div>
            <div class="field"><label>Category</label>
              <select id="a-category">${categories.map((c) => `<option value="${c}" ${c === "Other" ? "selected" : ""}>${c}</option>`).join("")}</select>
            </div>
            <div class="field"><label>Situation — what was happening?</label><textarea id="a-situation" rows="2"></textarea></div>
            <div class="field"><label>Task — what were you responsible for?</label><textarea id="a-task" rows="2"></textarea></div>
            <div class="field"><label>Action — what did you actually do?</label><textarea id="a-action" rows="2"></textarea></div>
            <div class="field"><label>Result — what changed?</label><textarea id="a-result" rows="2"></textarea></div>
            <div class="field"><label>Metric — can you quantify it?</label><input type="text" id="a-metric" /></div>
            <div class="field"><label>Skills (comma-separated)</label><input type="text" id="a-skills" /></div>
            <div class="field"><label>Related project</label><select id="a-project">${optionsHtml(projects, "id", "name")}</select></div>
            <div class="field"><label>Resume bullet (optional — auto-generated later if left blank)</label><textarea id="a-bullet" rows="2"></textarea></div>
            <div class="btn-row"><button type="submit" class="btn-primary">Save achievement</button></div>
          </form>
        </div>
      </details>

      <div class="section-gap" id="achievement-list"></div>
    `;

    const draftBtn = container.querySelector("#a-draft-btn");
    if (draftBtn) {
      draftBtn.addEventListener("click", () =>
        withBusy(draftBtn, async () => {
          const logId = container.querySelector("#a-source-log").value;
          if (!logId) return;
          const log = worklogs.find((l) => String(l.id) === logId);
          try {
            const star = await Api.suggestAchievement(log.raw_text, log.accomplishments || "");
            if (star.title) container.querySelector("#a-title").value = star.title;
            if (star.category && categories.includes(star.category)) container.querySelector("#a-category").value = star.category;
            container.querySelector("#a-situation").value = star.situation || "";
            container.querySelector("#a-task").value = star.task || "";
            container.querySelector("#a-action").value = star.action || "";
            container.querySelector("#a-result").value = star.result || "";
            container.querySelector("#a-metric").value = star.metric || "";
            container.querySelector("#a-skills").value = (star.skills || []).join(", ");
            toast("Draft generated — review before saving.");
          } catch (err) {
            toast(`Draft failed: ${err.message}`, true);
          }
        })
      );
    }

    container.querySelector("#achievement-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const title = container.querySelector("#a-title").value.trim();
      if (!title) return;
      const btn = e.target.querySelector("button[type=submit]");
      await withBusy(btn, async () => {
        try {
          await Api.createAchievement({
            title,
            category: container.querySelector("#a-category").value,
            situation: container.querySelector("#a-situation").value,
            task: container.querySelector("#a-task").value,
            action: container.querySelector("#a-action").value,
            result: container.querySelector("#a-result").value,
            metric: container.querySelector("#a-metric").value,
            skills: container.querySelector("#a-skills").value,
            resume_bullet: container.querySelector("#a-bullet").value,
            project_id: numOrNull(container.querySelector("#a-project").value),
          });
          toast(`Saved: ${title}`);
          Router.navigate();
        } catch (err) {
          toast(`Save failed: ${err.message}`, true);
        }
      });
    });

    renderList(container.querySelector("#achievement-list"), achievements);
  },
};

function numOrNull(value) {
  return value === "" ? null : Number(value);
}

function renderList(el, achievements) {
  if (!achievements.length) {
    el.innerHTML = emptyState("No achievements yet.");
    return;
  }
  const field = (label, value) => value ? `<div class="small" style="margin-bottom:6px;"><strong>${label}:</strong> ${escapeHtml(value)}</div>` : "";
  el.innerHTML = achievements.map((a) => `
    <details class="expandable">
      <summary>✓ ${escapeHtml(a.title)} <span class="badge blue">${escapeHtml(a.category || "Other")}</span></summary>
      <div class="section-gap">
        ${field("Situation", a.situation)}
        ${field("Task", a.task)}
        ${field("Action", a.action)}
        ${field("Result", a.result)}
        ${field("Metric", a.metric)}
        ${a.skills ? `<div class="small" style="margin-bottom:8px;"><strong>Skills:</strong> ${tagList(a.skills)}</div>` : ""}
        ${field("Resume bullet", a.resume_bullet)}
        <button class="btn-danger" data-del="${a.id}">Delete</button>
      </div>
    </details>
  `).join("");

  el.querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      if (!confirm("Delete this achievement?")) return;
      await Api.deleteAchievement(btn.dataset.del);
      Router.navigate();
    });
  });
}
