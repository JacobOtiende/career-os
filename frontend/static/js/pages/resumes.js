Pages.resumes = {
  async render(container) {
    const [profiles, jds, resumes] = await Promise.all([
      Api.resumeProfiles(), Api.jobs(), Api.resumes(),
    ]);

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Resume Generator</h1>
          <div class="page-subtitle">Every bullet traces back to an Achievement, then its Work Log / Project source.</div>
        </div>
      </div>

      <details class="expandable">
        <summary>Manage resume profiles</summary>
        <form id="profile-form" class="section-gap">
          <div class="field"><label>Profile name (e.g. 'IT Operations', 'Data Analytics', 'AI/ML')</label><input type="text" id="rp-name" required /></div>
          <div class="field"><label>Description</label><input type="text" id="rp-description" /></div>
          <div class="field"><label>Skills to emphasize (comma-separated)</label><input type="text" id="rp-skills" /></div>
          <div class="btn-row"><button type="submit" class="btn-secondary">Save profile</button></div>
        </form>
        <div class="section-gap" id="profile-list">
          ${profiles.length ? profiles.map((p) => `<div class="small"><strong>${escapeHtml(p.name)}</strong> — emphasizes: ${escapeHtml(p.emphasis_skills)}</div>`).join("") : emptyState("No profiles yet.")}
        </div>
      </details>

      <div class="card section-gap">
        <div class="form-row">
          <div class="field"><label>Resume profile (optional)</label><select id="gen-profile">${optionsHtml(profiles, "id", "name")}</select></div>
          <div class="field"><label>Target job description (optional)</label>
            <select id="gen-jd">${optionsHtml(jds.map((j) => ({ id: j.id, label: `${j.title || "Untitled"} (#${j.id})` })), "id", "label")}</select>
          </div>
        </div>
        <div class="field" style="max-width:220px">
          <label>Number of bullets</label>
          <input type="number" id="gen-top-n" min="3" max="15" value="8" />
        </div>
        <div class="btn-row"><button id="gen-btn" class="btn-primary">Generate resume</button></div>
      </div>

      <div class="card section-gap">
        <div class="field" style="max-width:420px">
          <label>View a generated resume</label>
          <select id="resume-select">${resumes.map((r) => `<option value="${r.id}">${escapeHtml(r.target_role)} — ${escapeHtml(new Date(r.created_at).toLocaleString())}</option>`).join("")}</select>
        </div>
        <div id="resume-detail"></div>
      </div>
    `;

    container.querySelector("#profile-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = container.querySelector("#rp-name").value.trim();
      if (!name) return;
      await Api.createResumeProfile({
        name,
        description: container.querySelector("#rp-description").value,
        emphasis_skills: container.querySelector("#rp-skills").value,
      });
      toast("Profile saved.");
      Router.navigate();
    });

    const genBtn = container.querySelector("#gen-btn");
    genBtn.addEventListener("click", () =>
      withBusy(genBtn, async () => {
        try {
          const profileId = container.querySelector("#gen-profile").value;
          const jdId = container.querySelector("#gen-jd").value;
          const resume = await Api.generateResume({
            profile_id: profileId ? Number(profileId) : null,
            job_description_id: jdId ? Number(jdId) : null,
            top_n: Number(container.querySelector("#gen-top-n").value) || 8,
          });
          toast("Resume generated.");
          Router.navigate();
        } catch (err) {
          toast(`Generation failed: ${err.message}`, true);
        }
      })
    );

    const detailEl = container.querySelector("#resume-detail");
    const resumeSelect = container.querySelector("#resume-select");
    if (!resumes.length) {
      detailEl.innerHTML = emptyState("No resumes generated yet.");
      return;
    }
    resumeSelect.addEventListener("change", () => loadResumeDetail(detailEl, resumeSelect.value));
    loadResumeDetail(detailEl, resumeSelect.value);
  },
};

async function loadResumeDetail(el, resumeId) {
  el.innerHTML = emptyState("Loading…");
  const resume = await Api.getResume(resumeId);

  el.innerHTML = `
    <h2 class="card-title section-gap">Resume: ${escapeHtml(resume.target_role)}</h2>
    ${resume.match_score !== null ? `<div class="stat-card" style="max-width:260px;"><div class="stat-label">Match score at generation</div><div class="stat-value">${resume.match_score}%</div></div>` : ""}

    <div class="entry-list section-gap">
      ${resume.bullets.map((b, i) => `
        <details class="expandable">
          <summary>${escapeHtml(b.text)}</summary>
          <div class="section-gap">
            ${b.evidence ? renderEvidenceChain(b.evidence) : `<span class="muted small">Source achievement was deleted.</span>`}
          </div>
        </details>
      `).join("")}
    </div>

    <div class="btn-row section-gap">
      <button id="download-resume-btn" class="btn-secondary">⬇️ Download as plain text</button>
    </div>
  `;

  el.querySelector("#download-resume-btn").addEventListener("click", () => {
    const text = resume.bullets.map((b) => `- ${b.text}`).join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `resume_${resume.target_role.replace(/\s+/g, "_")}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });
}

function renderEvidenceChain(a) {
  let chain = `
    <div class="evidence-chain">
      <div class="step"><span class="step-label">Achievement #${a.id}</span><div>${escapeHtml(a.title)}</div></div>
      <div class="step small muted">
        S: ${escapeHtml(a.situation || "—")}<br/>
        T: ${escapeHtml(a.task || "—")}<br/>
        A: ${escapeHtml(a.action || "—")}<br/>
        R: ${escapeHtml(a.result || "—")}<br/>
        Metric: ${escapeHtml(a.metric || "—")}
      </div>`;
  if (a.work_log) {
    chain += `<div class="step"><span class="step-label">Work Log — ${formatDate(a.work_log.date)}</span><div>${escapeHtml(a.work_log.raw_text)}</div></div>`;
  }
  if (a.project) {
    chain += `<div class="step"><span class="step-label">Project</span><div>${escapeHtml(a.project.name)}</div></div>`;
  }
  chain += `</div>`;
  return chain;
}
