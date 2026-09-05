const Api = (() => {
  async function request(method, path, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(`/api${path}`, opts);
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const data = await res.json();
        detail = data.detail || JSON.stringify(data);
      } catch (e) {}
      throw new Error(detail || `Request failed (${res.status})`);
    }
    if (res.status === 204) return null;
    const text = await res.text();
    return text ? JSON.parse(text) : null;
  }

  const get = (path) => request("GET", path);
  const post = (path, body) => request("POST", path, body || {});
  const del = (path) => request("DELETE", path);

  async function upload(path, file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`/api${path}`, { method: "POST", body: formData });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const data = await res.json();
        detail = data.detail || JSON.stringify(data);
      } catch (e) {}
      throw new Error(detail || `Upload failed (${res.status})`);
    }
    return res.json();
  }

  return {
    status: () => get("/status"),
    dashboard: () => get("/dashboard"),

    worklogs: () => get("/worklogs"),
    extractWorklog: (raw_text) => post("/worklogs/extract", { raw_text }),
    createWorklog: (payload) => post("/worklogs", payload),
    deleteWorklog: (id) => del(`/worklogs/${id}`),

    projects: () => get("/projects"),
    createProject: (payload) => post("/projects", payload),
    deleteProject: (id) => del(`/projects/${id}`),

    achievements: () => get("/achievements"),
    suggestAchievement: (raw_text, extra_context) => post("/achievements/suggest", { raw_text, extra_context }),
    createAchievement: (payload) => post("/achievements", payload),
    deleteAchievement: (id) => del(`/achievements/${id}`),

    skills: () => get("/skills"),
    skillEvidence: (id) => get(`/skills/${id}/evidence`),

    volunteer: () => get("/volunteer"),
    createVolunteer: (payload) => post("/volunteer", payload),
    deleteVolunteer: (id) => del(`/volunteer/${id}`),

    employments: () => get("/employments"),
    createEmployment: (payload) => post("/employments", payload),
    deleteEmployment: (id) => del(`/employments/${id}`),

    education: () => get("/education"),
    createEducation: (payload) => post("/education", payload),
    deleteEducation: (id) => del(`/education/${id}`),

    certifications: () => get("/certifications"),
    createCertification: (payload) => post("/certifications", payload),
    deleteCertification: (id) => del(`/certifications/${id}`),

    timeline: () => get("/timeline"),

    jobs: () => get("/jobs"),
    createJob: (payload) => post("/jobs", payload),
    getJob: (id) => get(`/jobs/${id}`),

    resumeProfiles: () => get("/resume-profiles"),
    createResumeProfile: (payload) => post("/resume-profiles", payload),

    resumes: () => get("/resumes"),
    generateResume: (payload) => post("/resumes", payload),
    getResume: (id) => get(`/resumes/${id}`),

    exportTables: () => get("/export/tables"),
    exportTable: (name) => get(`/export/table/${name}`),

    resumeImports: () => get("/resume-imports"),
    uploadResumeImport: (file) => upload("/resume-imports", file),
    getResumeImport: (id) => get(`/resume-imports/${id}`),
    importBullet: (importId, index, payload) => post(`/resume-imports/${importId}/bullets/${index}/import`, payload),
    deleteResumeImport: (id) => del(`/resume-imports/${id}`),
  };
})();
