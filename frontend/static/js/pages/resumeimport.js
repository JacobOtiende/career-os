Pages.resumeimport = {
  async render(container) {
    const imports = await Api.resumeImports();

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Import Past Resumes</h1>
          <div class="page-subtitle">Upload an old resume (PDF, DOCX, or TXT) and pull its bullets into your evidence bank as Achievements.</div>
        </div>
      </div>

      <div class="card">
        <h2 class="card-title">Upload a resume</h2>
        <div class="field">
          <label>File</label>
          <input type="file" id="resume-file" accept=".pdf,.docx,.txt,.md" />
          <div class="hint">Nothing here rewrites your resume automatically — every bullet is a suggestion you review and import one at a time.</div>
        </div>
        <div class="btn-row">
          <button id="upload-btn" class="btn-primary" disabled>Upload &amp; parse</button>
        </div>
      </div>

      <div class="card section-gap">
        <div class="field" style="max-width:420px">
          <label>Previously uploaded</label>
          <select id="import-select">
            ${imports.map((i) => `<option value="${i.id}">${escapeHtml(i.filename)} — ${i.imported_count}/${i.bullet_count} imported</option>`).join("")}
          </select>
        </div>
        <div id="import-detail"></div>
      </div>
    `;

    const fileInput = container.querySelector("#resume-file");
    const uploadBtn = container.querySelector("#upload-btn");
    fileInput.addEventListener("change", () => { uploadBtn.disabled = !fileInput.files.length; });

    uploadBtn.addEventListener("click", () =>
      withBusy(uploadBtn, async () => {
        const file = fileInput.files[0];
        if (!file) return;
        try {
          await Api.uploadResumeImport(file);
          toast(`Parsed ${file.name}.`);
          Router.navigate();
        } catch (err) {
          toast(`Upload failed: ${err.message}`, true);
        }
      })
    );

    const select = container.querySelector("#import-select");
    const detail = container.querySelector("#import-detail");
    if (!imports.length) {
      detail.innerHTML = emptyState("No resumes uploaded yet.");
      return;
    }
    select.addEventListener("change", () => loadImportDetail(detail, select.value));
    loadImportDetail(detail, select.value);
  },
};

async function loadImportDetail(el, importId) {
  el.innerHTML = emptyState("Loading…");
  const record = await Api.getResumeImport(importId);

  el.innerHTML = `
    <div class="btn-row" style="justify-content:space-between;align-items:center;">
      <div class="small muted">Uploaded ${formatDate(record.uploaded_at)}</div>
      <button class="btn-danger" id="delete-import-btn">Delete this upload</button>
    </div>
    <details class="expandable section-gap">
      <summary>View extracted raw text</summary>
      <pre class="section-gap small" style="white-space:pre-wrap;">${escapeHtml(record.raw_text)}</pre>
    </details>
    <div class="entry-list section-gap" id="bullet-list"></div>
  `;

  el.querySelector("#delete-import-btn").addEventListener("click", async () => {
    if (!confirm("Delete this uploaded resume and its parsed bullets? Already-imported achievements are kept.")) return;
    await Api.deleteResumeImport(importId);
    toast("Deleted.");
    Router.navigate();
  });

  const list = el.querySelector("#bullet-list");
  const categories = ["Leadership", "Technical", "Analytics", "Process Improvement", "Other"];

  list.innerHTML = record.bullets.length
    ? record.bullets.map((b, i) => `
        <div class="entry-item">
          <div class="entry-item-body" style="margin-top:0;">${escapeHtml(b.text)}</div>
          ${b.imported
            ? `<div class="btn-row"><span class="badge green">✓ Imported as Achievement #${b.achievement_id}</span></div>`
            : `
              <div class="form-row section-gap">
                <div class="field"><label>Title</label><input type="text" class="bullet-title" value="${escapeHtml(b.title)}" /></div>
                <div class="field"><label>Category</label>
                  <select class="bullet-category">
                    ${categories.map((c) => `<option value="${c}" ${c === (b.category || "Other") ? "selected" : ""}>${c}</option>`).join("")}
                  </select>
                </div>
              </div>
              <div class="field"><label>Skills (comma-separated)</label><input type="text" class="bullet-skills" value="${escapeHtml((b.skills || []).join(", "))}" /></div>
              <div class="btn-row">
                <button class="btn-secondary bullet-import-btn" data-index="${i}">Import as Achievement</button>
              </div>
            `}
        </div>
      `).join("")
    : emptyState("No candidate bullets were found in this file.");

  list.querySelectorAll(".bullet-import-btn").forEach((btn) => {
    btn.addEventListener("click", () =>
      withBusy(btn, async () => {
        const index = Number(btn.dataset.index);
        const item = list.querySelectorAll(".entry-item")[index];
        const title = item.querySelector(".bullet-title").value;
        const category = item.querySelector(".bullet-category").value;
        const skills = item.querySelector(".bullet-skills").value;
        try {
          await Api.importBullet(importId, index, { title, category, skills });
          toast("Imported as an Achievement.");
          loadImportDetail(el, importId);
        } catch (err) {
          toast(`Import failed: ${err.message}`, true);
        }
      })
    );
  });
}
