Pages.worklog = {
  async render(container) {
    const [employments, projects, volunteers, logs] = await Promise.all([
      Api.employments(), Api.projects(), Api.volunteer(), Api.worklogs(),
    ]);

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Daily Work Log</h1>
          <div class="page-subtitle">Write in plain language. AI suggests structure — you confirm or edit before saving.</div>
        </div>
      </div>

      <details class="expandable">
        <summary>Quick-add an employer (optional)</summary>
        <form id="employer-form" class="section-gap">
          <div class="form-row">
            <div class="field"><label>Organization</label><input type="text" id="qe-org" /></div>
            <div class="field"><label>Role</label><input type="text" id="qe-role" /></div>
          </div>
          <label class="small"><input type="checkbox" id="qe-current" checked /> Current position</label>
          <div class="btn-row"><button type="submit" class="btn-secondary">Add employer</button></div>
        </form>
      </details>

      <div class="card section-gap">
        <div class="form-row">
          <div class="field"><label>Date</label><input type="date" id="wl-date" value="${todayStr()}" /></div>
          <div class="field"><label>Hours worked</label><input type="number" id="wl-hours" min="0" max="24" step="0.25" value="0" /></div>
        </div>
        <div class="form-row">
          <div class="field"><label>Employer</label><select id="wl-employment">${optionsHtml(employments, "id", "organization")}</select></div>
          <div class="field"><label>Related project</label><select id="wl-project">${optionsHtml(projects, "id", "name")}</select></div>
          <div class="field"><label>Volunteer org (if applicable)</label><select id="wl-volunteer">${optionsHtml(volunteers, "id", "organization")}</select></div>
        </div>
        <div class="field">
          <label>Category</label>
          <select id="wl-category">
            <option value="regular">regular</option>
            <option value="project">project</option>
            <option value="training">training</option>
            <option value="professional_development">professional_development</option>
            <option value="volunteer">volunteer</option>
          </select>
        </div>
        <div class="field">
          <label>What did you work on today?</label>
          <textarea id="wl-raw-text" rows="4" placeholder="Spent 3 hours troubleshooting a Windows deployment issue affecting 12 workstations. Identified an imaging configuration problem and worked with the vendor to resolve it."></textarea>
        </div>
        <div class="field"><label>Who did you work with? (optional)</label><input type="text" id="wl-collaborators" /></div>

        <div class="btn-row">
          <button id="wl-extract-btn" class="btn-secondary" disabled>🤖 Extract structure with AI</button>
        </div>

        <hr class="divider" />
        <h2 class="card-title">Structured evidence (review and edit before saving)</h2>
        <div class="field"><label>Problems solved</label><textarea id="wl-problems" rows="2"></textarea></div>
        <div class="field"><label>Accomplishments</label><textarea id="wl-accomplishments" rows="2"></textarea></div>
        <div class="field"><label>Tools/technologies used (comma-separated)</label><input type="text" id="wl-tools" /></div>
        <div class="field"><label>Skills demonstrated (comma-separated)</label><input type="text" id="wl-skills" /></div>
        <div class="field"><label>Anything worth remembering? (optional)</label><textarea id="wl-notes" rows="2"></textarea></div>

        <div class="btn-row">
          <button id="wl-save-btn" class="btn-primary" disabled>💾 Save entry</button>
        </div>
      </div>

      <div class="card section-gap">
        <h2 class="card-title">Recent entries</h2>
        <div id="wl-recent"></div>
      </div>
    `;

    const rawText = container.querySelector("#wl-raw-text");
    const extractBtn = container.querySelector("#wl-extract-btn");
    const saveBtn = container.querySelector("#wl-save-btn");

    const updateButtons = () => {
      const has = rawText.value.trim().length > 0;
      extractBtn.disabled = !has;
      saveBtn.disabled = !has;
    };
    rawText.addEventListener("input", updateButtons);
    updateButtons();

    let aiProcessed = false;

    extractBtn.addEventListener("click", () =>
      withBusy(extractBtn, async () => {
        try {
          const result = await Api.extractWorklog(rawText.value);
          container.querySelector("#wl-problems").value = result.problems_solved || "";
          container.querySelector("#wl-accomplishments").value = result.accomplishments || "";
          container.querySelector("#wl-tools").value = (result.tools_used || []).join(", ");
          container.querySelector("#wl-skills").value = (result.skills || []).join(", ");
          if (result.hours_mentioned && Number(container.querySelector("#wl-hours").value) === 0) {
            container.querySelector("#wl-hours").value = result.hours_mentioned;
          }
          aiProcessed = true;
          toast("Extraction complete — review before saving.");
        } catch (err) {
          toast(`Extraction failed: ${err.message}`, true);
        }
      })
    );

    container.querySelector("#employer-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const organization = container.querySelector("#qe-org").value.trim();
      if (!organization) return;
      await Api.createEmployment({
        organization,
        role: container.querySelector("#qe-role").value.trim(),
        is_current: container.querySelector("#qe-current").checked,
        start_date: todayStr(),
      });
      toast(`Added ${organization}`);
      Router.navigate();
    });

    saveBtn.addEventListener("click", () =>
      withBusy(saveBtn, async () => {
        const payload = {
          date: container.querySelector("#wl-date").value,
          employment_id: numOrNull(container.querySelector("#wl-employment").value),
          project_id: numOrNull(container.querySelector("#wl-project").value),
          volunteer_org_id: numOrNull(container.querySelector("#wl-volunteer").value),
          category: container.querySelector("#wl-category").value,
          hours: Number(container.querySelector("#wl-hours").value) || 0,
          raw_text: rawText.value,
          problems_solved: container.querySelector("#wl-problems").value,
          accomplishments: container.querySelector("#wl-accomplishments").value,
          collaborators: container.querySelector("#wl-collaborators").value,
          tools_used: container.querySelector("#wl-tools").value,
          skills: container.querySelector("#wl-skills").value,
          notes: container.querySelector("#wl-notes").value,
          ai_processed: aiProcessed,
        };
        if (!payload.raw_text.trim()) return;
        try {
          await Api.createWorklog(payload);
          toast("Saved. Skills evidence recorded.");
          Router.navigate();
        } catch (err) {
          toast(`Save failed: ${err.message}`, true);
        }
      })
    );

    renderRecent(container.querySelector("#wl-recent"), logs);
  },
};

function numOrNull(value) {
  return value === "" ? null : Number(value);
}

function renderRecent(el, logs) {
  if (!logs.length) {
    el.innerHTML = emptyState("No entries yet.");
    return;
  }
  el.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Date</th><th>Hours</th><th>Category</th><th>Summary</th><th>Skills</th><th></th></tr></thead>
        <tbody>
          ${logs.slice(0, 25).map((l) => `
            <tr>
              <td>${formatDate(l.date)}</td>
              <td>${l.hours}</td>
              <td><span class="badge gray">${escapeHtml(l.category)}</span></td>
              <td>${escapeHtml(l.raw_text.slice(0, 100))}${l.raw_text.length > 100 ? "…" : ""}</td>
              <td>${tagList(l.skills)}</td>
              <td><button class="btn-danger" data-del="${l.id}">Delete</button></td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
  el.querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this work log entry?")) return;
      await Api.deleteWorklog(btn.dataset.del);
      Router.navigate();
    });
  });
}
