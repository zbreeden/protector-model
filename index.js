// protector-model index page JS: lazy-load external markdown toggle and disable CTA if model assets missing
document.addEventListener('DOMContentLoaded', () => {
  // Find or create the elements near the model CTA
  let cta = document.querySelector('a.cta[href="./model.html"]');
  if (!cta) return; // nothing to do
  const parent = cta.parentElement || document.body;

  // Create toggle button (next to CTA) if missing
  let toggle = parent.querySelector('.doc-toggle');
  if (!toggle) {
    toggle = document.createElement('button');
    toggle.className = 'doc-toggle';
    toggle.type = 'button';
    toggle.setAttribute('aria-pressed', 'false');
    toggle.setAttribute('data-src', './data/external/fraud.md');
    toggle.textContent = 'Show Project Document';
    parent.appendChild(toggle);
  }

  // Create meta/title element below the toggle (if missing)
  let meta = parent.querySelector('.doc-meta');
  if (!meta) {
    meta = document.createElement('div'); meta.className = 'doc-meta'; meta.textContent = 'This model is in development.';
    parent.appendChild(meta);
  }

  // Create container for markdown
  let container = parent.querySelector('.external-markdown');
  if (!container) {
    container = document.createElement('div'); container.className = 'external-markdown'; container.style.display = 'none';
    parent.appendChild(container);
  }

  // Helper to fetch and render markdown safely
  async function fetchAndRender(url) {
    toggle.disabled = true;
    try {
      const res = await fetch(url, { cache: 'no-cache' });
      if (!res.ok) throw new Error('Fetch failed: ' + res.status);
      const md = await res.text();
      const titleMatch = md.match(/^#\s+(.*)/m);
      if (titleMatch) meta.textContent = titleMatch[1];
      if (window.marked && window.DOMPurify) {
        const html = window.marked.parse(md);
        container.innerHTML = window.DOMPurify.sanitize(html);
      } else {
        const pre = document.createElement('pre'); pre.textContent = md; container.appendChild(pre);
      }
    } catch (err) {
      container.innerHTML = '<p class="subtle">Unable to load document.</p>';
      console.error('Error loading external markdown:', err);
    } finally {
      toggle.disabled = false;
    }
  }

  let loaded = false;
  toggle.addEventListener('click', async () => {
    const isOpen = toggle.getAttribute('aria-pressed') === 'true';
    if (isOpen) {
      container.style.display = 'none';
      toggle.setAttribute('aria-pressed', 'false');
      toggle.textContent = 'Show Project Document';
      return;
    }
    container.style.display = '';
    toggle.setAttribute('aria-pressed', 'true');
    toggle.textContent = 'Hide Project Document';
    if (!loaded) {
      const src = toggle.getAttribute('data-src') || './data/external/fraud.md';
      await fetchAndRender(src);
      loaded = true;
    }
  });

  // Asset existence check: HEAD then GET fallback
  async function assetExists(path) {
    try {
      const head = await fetch(path, { method: 'HEAD' });
      if (head && head.ok) return true;
    } catch (e) {}
    try {
      const get = await fetch(path, { method: 'GET' });
      return get && get.ok;
    } catch (e) { return false; }
  }

  (async function checkModelAssets() {
    const checks = await Promise.all([
      assetExists('./model.html'), assetExists('./model.js'), assetExists('./model.css')
    ]);
    if (!checks.some(Boolean)) {
      // disable CTA and update label
      cta.classList.add('disabled');
      cta.setAttribute('aria-disabled', 'true');
      cta.setAttribute('tabindex', '-1');
      cta.style.pointerEvents = 'none';
      cta.style.opacity = '0.6';
        cta.textContent = 'Model in Development';
        // Insert inline visible hint with the model title (from header)
        try {
          const header = document.querySelector('header');
          let modelTitle = '';
          if (header) {
            const p = header.querySelector('p');
            const h1 = header.querySelector('h1');
            if (p && p.textContent.trim()) modelTitle = p.textContent.trim();
            else if (h1 && h1.textContent.trim()) modelTitle = h1.textContent.trim().replace(/^[^\w\d]+/, '').trim();
          }
          if (modelTitle) {
            let hint = cta.parentElement.querySelector('.model-hint');
            if (!hint) {
              hint = document.createElement('div'); hint.className = 'model-hint'; hint.textContent = modelTitle; cta.parentElement.appendChild(hint);
            } else { hint.textContent = modelTitle; }
          }
        } catch (e) { }
      cta.addEventListener('click', (ev) => { ev.preventDefault(); }, { capture: true });
    }
  })();
});
