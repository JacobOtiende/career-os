Pages.career = {
  async render(container) {
    container.innerHTML = `
      <div class="page-header"><h1 class="page-title">Career Journey</h1></div>
      <div class="btn-row" id="career-tabs">
        <button class="btn-secondary tab-btn active" data-tab="employment">Employment</button>
        <button class="btn-secondary tab-btn" data-tab="education">Education</button>
        <button class="btn-secondary tab-btn" data-tab="certifications">Certifications</button>
        <button class="btn-secondary tab-btn" data-tab="timeline">Timeline</button>
      </div>
      <div class="section-gap" id="career-panel"></div>
    `;

    const panel = container.querySelector("#career-panel");
    const tabButtons = [...container.querySelectorAll(".tab-btn")];

    const panels = { employment: renderEmployment, education: renderEducation, certifications: renderCertifications, timeline: renderTimeline };

    async function showTab(tab) {
      tabButtons.forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
      tabButtons.forEach((b) => b.style.background = b.dataset.tab === tab ? "var(--accent-soft)" : "");
      panel.innerHTML = emptyState("Loading…");
      await panels[tab](panel);
    }

    tabButtons.forEach((btn) => btn.addEventListener("click", () => showTab(btn.dataset.tab)));
    showTab("employment");
  },
};

async function renderEmployment(panel) {
  const employments = await Api.employments();
  panel.innerHTML = `
    <details class="expandable">
      <summary>Add employment</summary>
      <form id="emp-form" class="section-gap">
        <div class="field"><label>Organization*</label><input type="text" id="emp-org" required /></div>
        <div class="field"><label>Role*</label><input type="text" id="emp-role" required /></div>
        <div class="form-row">
          <div class="field"><label>Start Date</label><input type="date" id="emp-start" value="${todayStr()}" /></div>
          <div class="field"><label>End Date</label><input type="date" id="emp-end" /></div>
        </div>
        <label class="small"><input type="checkbox" id="emp-current" checked /> Current</label>
        <div class="btn-row"><button type="submit" class="btn-primary">Save</button></div>
      </form>
    </details>
    <div class="card section-gap">
      ${employments.length ? employments.map((e) => `
        <div class="entry-item">
          <div class="entry-item-head">
            <span class="entry-item-title">${escapeHtml(e.organization)} — ${escapeHtml(e.role)}</span>
            <button class="btn-danger" data-del="${e.id}">Delete</button>
          </div>
          <div class="entry-item-body">${formatDate(e.start_date)} – ${e.is_current ? "present" : formatDate(e.end_date)}</div>
        </div>`).join("") : emptyState("No employment history yet.")}
    </div>
  `;
  panel.querySelector("#emp-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const organization = panel.querySelector("#emp-org").value.trim();
    const role = panel.querySelector("#emp-role").value.trim();
    if (!organization || !role) return;
    await Api.createEmployment({
      organization, role,
      start_date: panel.querySelector("#emp-start").value || null,
      end_date: panel.querySelector("#emp-end").value || null,
      is_current: panel.querySelector("#emp-current").checked,
    });
    toast("Saved");
    renderEmployment(panel);
  });
  panel.querySelectorAll("[data-del]").forEach((btn) => btn.addEventListener("click", async () => {
    if (!confirm("Delete this employment record?")) return;
    await Api.deleteEmployment(btn.dataset.del);
    renderEmployment(panel);
  }));
}

async function renderEducation(panel) {
  const items = await Api.education();
  panel.innerHTML = `
    <details class="expandable">
      <summary>Add education</summary>
      <form id="edu-form" class="section-gap">
        <div class="field"><label>School*</label><input type="text" id="edu-school" required /></div>
        <div class="form-row">
          <div class="field"><label>Degree</label><input type="text" id="edu-degree" /></div>
          <div class="field"><label>Field of study</label><input type="text" id="edu-field" /></div>
        </div>
        <div class="form-row">
          <div class="field"><label>Start Date</label><input type="date" id="edu-start" /></div>
          <div class="field"><label>End Date</label><input type="date" id="edu-end" /></div>
        </div>
        <div class="btn-row"><button type="submit" class="btn-primary">Save</button></div>
      </form>
    </details>
    <div class="card section-gap">
      ${items.length ? items.map((e) => `
        <div class="entry-item">
          <div class="entry-item-head">
            <span class="entry-item-title">${escapeHtml(e.school)}</span>
            <button class="btn-danger" data-del="${e.id}">Delete</button>
          </div>
          <div class="entry-item-body">${escapeHtml(e.degree || "")} ${e.field ? "in " + escapeHtml(e.field) : ""} · ${formatDate(e.start_date)} – ${e.end_date ? formatDate(e.end_date) : "present"}</div>
        </div>`).join("") : emptyState("No education records yet.")}
    </div>
  `;
  panel.querySelector("#edu-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const school = panel.querySelector("#edu-school").value.trim();
    if (!school) return;
    await Api.createEducation({
      school,
      degree: panel.querySelector("#edu-degree").value,
      field: panel.querySelector("#edu-field").value,
      start_date: panel.querySelector("#edu-start").value || null,
      end_date: panel.querySelector("#edu-end").value || null,
    });
    toast("Saved");
    renderEducation(panel);
  });
  panel.querySelectorAll("[data-del]").forEach((btn) => btn.addEventListener("click", async () => {
    if (!confirm("Delete this education record?")) return;
    await Api.deleteEducation(btn.dataset.del);
    renderEducation(panel);
  }));
}

async function renderCertifications(panel) {
  const items = await Api.certifications();
  panel.innerHTML = `
    <details class="expandable">
      <summary>Add certification</summary>
      <form id="cert-form" class="section-gap">
        <div class="field"><label>Certification name*</label><input type="text" id="cert-name" required /></div>
        <div class="field"><label>Issuer</label><input type="text" id="cert-issuer" /></div>
        <div class="form-row">
          <div class="field"><label>Date earned</label><input type="date" id="cert-earned" value="${todayStr()}" /></div>
          <div class="field"><label>Expires</label><input type="date" id="cert-expires" /></div>
        </div>
        <div class="btn-row"><button type="submit" class="btn-primary">Save</button></div>
      </form>
    </details>
    <div class="card section-gap">
      ${items.length ? items.map((c) => `
        <div class="entry-item">
          <div class="entry-item-head">
            <span class="entry-item-title">${escapeHtml(c.name)}</span>
            <button class="btn-danger" data-del="${c.id}">Delete</button>
          </div>
          <div class="entry-item-body">${escapeHtml(c.issuer || "")} · earned ${formatDate(c.date_earned)}${c.expires ? " · expires " + formatDate(c.expires) : ""}</div>
        </div>`).join("") : emptyState("No certifications yet.")}
    </div>
  `;
  panel.querySelector("#cert-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = panel.querySelector("#cert-name").value.trim();
    if (!name) return;
    await Api.createCertification({
      name,
      issuer: panel.querySelector("#cert-issuer").value,
      date_earned: panel.querySelector("#cert-earned").value || null,
      expires: panel.querySelector("#cert-expires").value || null,
    });
    toast("Saved");
    renderCertifications(panel);
  });
  panel.querySelectorAll("[data-del]").forEach((btn) => btn.addEventListener("click", async () => {
    if (!confirm("Delete this certification?")) return;
    await Api.deleteCertification(btn.dataset.del);
    renderCertifications(panel);
  }));
}

async function renderTimeline(panel) {
  const events = await Api.timeline();
  panel.innerHTML = `
    <div class="card">
      <div class="small muted" style="margin-bottom:12px;">Auto-built from employment, project, and achievement dates.</div>
      ${events.length ? `<div class="evidence-chain">${events.map((e) => `
        <div class="step"><span class="step-label">${formatDate(e.date)}</span><div>${escapeHtml(e.label)}</div></div>
      `).join("")}</div>` : emptyState("No timeline events yet — add employment, projects, or achievements.")}
    </div>
  `;
}
