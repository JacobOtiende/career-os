const Router = (() => {
  const content = document.getElementById("content");
  const links = document.querySelectorAll(".nav-link[data-route]");
  let currentToken = 0;

  function routeFromHash() {
    const hash = window.location.hash.replace(/^#\/?/, "");
    return hash && Pages[hash] ? hash : "dashboard";
  }

  async function navigate() {
    const route = routeFromHash();
    const token = ++currentToken;

    links.forEach((l) => l.classList.toggle("active", l.dataset.route === route));

    const page = Pages[route];
    if (!page) {
      content.innerHTML = emptyState("Page not found.");
      return;
    }
    content.innerHTML = `<div class="empty-state">Loading…</div>`;
    try {
      await page.render(content);
      if (token !== currentToken) return;
    } catch (err) {
      if (token !== currentToken) return;
      content.innerHTML = emptyState(`Failed to load page: ${err.message}`);
      console.error(err);
    }
  }

  function init() {
    links.forEach((link) => {
      link.addEventListener("click", () => {
        window.location.hash = `/${link.dataset.route}`;
      });
    });
    window.addEventListener("hashchange", navigate);
    navigate();
  }

  return { init, navigate, get currentRoute() { return routeFromHash(); } };
})();

async function loadAiBadge() {
  const badge = document.getElementById("ai-badge");
  try {
    const status = await Api.status();
    if (status.llm_available) {
      badge.textContent = "AI extraction: ON";
      badge.className = "ai-badge on";
    } else {
      badge.textContent = "AI extraction: OFF (rule-based)";
      badge.className = "ai-badge off";
    }
  } catch (err) {
    badge.textContent = "API unreachable";
    badge.className = "ai-badge off";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadAiBadge();
  Router.init();
});
