Pages.projects = {
  async render(container) {
    const projects = await Api.projects();

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Project Portfolio</h1>
          <div class="page-subtitle">Every significant project gets its own record.</div>
        </div>
      </div>

      <details class="expandable">
        <summary>Add a project</summary>
        <form id="project-form" class="section-gap">
          <div class="form-row">
            <div class="field"><label>Project Name*</label><input type="text" id="p-name" required /></div>
            <div class="field"><label>Organization</label><input type="text" id="p-org" /></div>
            <div class="field"><label>Your Role</label><input type="text" id="p-role" /></div>
          </div>
          <div class="form-row">
            <div class="field"><label>Start Date</label><input type="date" id="p-start" value="${todayStr()}" /></div>
            <div class="field"><label>End Date</label><input type="date" id="p-end" /></div>
            <div class="field"><label>Status</label>
              <select id="p-status">
                <option value="planned">planned</option>
                <option value="active" selected>active</option>
                <option value="completed">completed</option>
                <option value="on_hold">on_hold</option>
              </select>
            </div>
          </div>
          <div class="field"><label>Problem</label><textarea id="p-problem" rows="2"></textarea></div>
          <div class="field"><label>Objective</label><textarea id="p-objective" rows="2"></textarea></div>
          <div class="field"><label>Responsibilities</label><textarea id="p-responsibilities" rows="2"></textarea></div>
          <div class="form-row">
            <div class="field"><label>Technologies (comma-separated)</label><input type="text" id="p-technologies" /></div>
            <div class="field"><label>Tools (comma-separated)</label><input type="text" id="p-tools" /></div>
            <div class="field"><label>Methods</label><input type="text" id="p-methods" /></div>
          </div>
          <div class="field"><label>Challenges</label><textarea id="p-challenges" rows="2"></textarea></div>
          <div class="field"><label>Solutions</label><textarea id="p-solutions" rows="2"></textarea></div>
          <div class="field"><label>Results</label><textarea id="p-results" rows="2"></textarea></div>
          <div class="form-row">
            <div class="field"><label>Metrics</label><input type="text" id="p-metrics" /></div>
            <div class="field"><label>People / Teams</label><input type="text" id="p-people" /></div>
          </div>
          <div class="field"><label>Leadership</label><textarea id="p-leadership" rows="2"></textarea></div>
          <div class="field"><label>Lessons Learned</label><textarea id="p-lessons" rows="2"></textarea></div>
          <div class="btn-row"><button type="submit" class="btn-primary">Save project</button></div>
        </form>
      </details>

      <div class="section-gap" id="project-list"></div>
    `;

    container.querySelector("#project-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = container.querySelector("#p-name").value.trim();
      if (!name) return;
      const btn = e.target.querySelector("button[type=submit]");
      await withBusy(btn, async () => {
        try {
          await Api.createProject({
            name,
            organization: container.querySelector("#p-org").value,
            role: container.querySelector("#p-role").value,
            status: container.querySelector("#p-status").value,
            start_date: container.querySelector("#p-start").value || null,
            end_date: container.querySelector("#p-end").value || null,
            problem: container.querySelector("#p-problem").value,
            objective: container.querySelector("#p-objective").value,
            responsibilities: container.querySelector("#p-responsibilities").value,
            technologies: container.querySelector("#p-technologies").value,
            tools: container.querySelector("#p-tools").value,
            methods: container.querySelector("#p-methods").value,
            challenges: container.querySelector("#p-challenges").value,
            solutions: container.querySelector("#p-solutions").value,
            results: container.querySelector("#p-results").value,
            metrics: container.querySelector("#p-metrics").value,
            people_teams: container.querySelector("#p-people").value,
            leadership: container.querySelector("#p-leadership").value,
            lessons_learned: container.querySelector("#p-lessons").value,
          });
          toast(`Saved ${name}`);
          Router.navigate();
        } catch (err) {
          toast(`Save failed: ${err.message}`, true);
        }
      });
    });

    renderList(container.querySelector("#project-list"), projects);
  },
};

function renderList(el, projects) {
  if (!projects.length) {
    el.innerHTML = emptyState("No projects yet.");
    return;
  }
  const field = (label, value) => value ? `<div class="field"><label>${label}</label><div>${escapeHtml(value)}</div></div>` : "";
  el.innerHTML = projects.map((p) => `
    <details class="expandable">
      <summary>${p.status === "active" ? "●" : "○"} ${escapeHtml(p.name)} — ${escapeHtml(p.organization || "—")}
        <span class="badge blue">${escapeHtml(p.status)}</span>
      </summary>
      <div class="section-gap">
        <div class="small muted">Role: ${escapeHtml(p.role || "—")} · ${formatDate(p.start_date)} – ${p.end_date ? formatDate(p.end_date) : "present"}</div>
        ${field("Objective", p.objective)}
        ${field("Responsibilities", p.responsibilities)}
        ${field("Technologies", p.technologies)}
        ${field("Tools", p.tools)}
        ${field("Challenges", p.challenges)}
        ${field("Solutions", p.solutions)}
        ${field("Results", p.results)}
        ${field("Metrics", p.metrics)}
        ${field("Leadership", p.leadership)}
        ${field("Lessons Learned", p.lessons_learned)}
        <button class="btn-danger" data-del="${p.id}">Delete project</button>
      </div>
    </details>
  `).join("");

  el.querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      if (!confirm("Delete this project?")) return;
      await Api.deleteProject(btn.dataset.del);
      Router.navigate();
    });
  });
}
