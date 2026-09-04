Pages.volunteer = {
  async render(container) {
    const orgs = await Api.volunteer();

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Volunteer &amp; Community Experience</h1>
        </div>
      </div>

      <details class="expandable">
        <summary>Add a volunteer organization</summary>
        <form id="vol-form" class="section-gap">
          <div class="field"><label>Organization*</label><input type="text" id="v-org" required /></div>
          <div class="field"><label>Role</label><input type="text" id="v-role" /></div>
          <div class="form-row">
            <div class="field"><label>Start Date</label><input type="date" id="v-start" value="${todayStr()}" /></div>
            <div class="field"><label>End Date</label><input type="date" id="v-end" /></div>
          </div>
          <div class="field"><label>Responsibilities</label><textarea id="v-responsibilities" rows="2"></textarea></div>
          <div class="field"><label>Community Impact</label><textarea id="v-impact" rows="2"></textarea></div>
          <div class="field"><label>Events / Presentations</label><textarea id="v-events" rows="2"></textarea></div>
          <div class="field"><label>Partnerships</label><input type="text" id="v-partnerships" /></div>
          <div class="btn-row"><button type="submit" class="btn-primary">Save</button></div>
        </form>
      </details>

      <div class="section-gap" id="vol-list"></div>
    `;

    container.querySelector("#vol-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const organization = container.querySelector("#v-org").value.trim();
      if (!organization) return;
      const btn = e.target.querySelector("button[type=submit]");
      await withBusy(btn, async () => {
        try {
          await Api.createVolunteer({
            organization,
            role: container.querySelector("#v-role").value,
            start_date: container.querySelector("#v-start").value || null,
            end_date: container.querySelector("#v-end").value || null,
            responsibilities: container.querySelector("#v-responsibilities").value,
            community_impact: container.querySelector("#v-impact").value,
            events: container.querySelector("#v-events").value,
            partnerships: container.querySelector("#v-partnerships").value,
          });
          toast(`Saved ${organization}`);
          Router.navigate();
        } catch (err) {
          toast(`Save failed: ${err.message}`, true);
        }
      });
    });

    const listEl = container.querySelector("#vol-list");
    if (!orgs.length) {
      listEl.innerHTML = emptyState("No volunteer experience recorded yet.");
      return;
    }
    const field = (label, value) => value ? `<div class="small" style="margin-bottom:6px;"><strong>${label}:</strong> ${escapeHtml(value)}</div>` : "";
    listEl.innerHTML = orgs.map((v) => `
      <details class="expandable">
        <summary>${escapeHtml(v.organization)} — ${escapeHtml(v.role || "—")} <span class="badge green">${v.logged_hours.toFixed(1)}h logged</span></summary>
        <div class="section-gap">
          <div class="small muted">${formatDate(v.start_date)} – ${v.end_date ? formatDate(v.end_date) : "present"}</div>
          ${field("Responsibilities", v.responsibilities)}
          ${field("Community Impact", v.community_impact)}
          ${field("Events/Presentations", v.events)}
          ${field("Partnerships", v.partnerships)}
          <div class="small muted">Log volunteer hours on the Daily Work Log page (select this org, category = volunteer).</div>
          <button class="btn-danger" data-del="${v.id}">Delete</button>
        </div>
      </details>
    `).join("");

    listEl.querySelectorAll("[data-del]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        if (!confirm("Delete this volunteer organization?")) return;
        await Api.deleteVolunteer(btn.dataset.del);
        Router.navigate();
      });
    });
  },
};
