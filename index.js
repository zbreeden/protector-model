// Minimal protector-model script: model dev button and README toggle for fraud.md only
document.addEventListener('DOMContentLoaded', () => {
  const modelBtn = document.getElementById('model-btn');
  const readmeToggle = document.getElementById('readme-toggle');
  const readmeContainer = document.getElementById('readme-container');

  // Model button: when clicked, simply show the text "Model in Development" inline
  if (modelBtn) {
    modelBtn.addEventListener('click', (ev) => {
      ev.preventDefault();
      // show a simple inline message next to the button (no tooltips/popups)
      let msg = modelBtn.parentElement.querySelector('.simple-model-message');
      if (!msg) {
        msg = document.createElement('div');
        msg.className = 'simple-model-message';
        msg.style.display = 'inline-block';
        msg.style.marginLeft = '0.6rem';
        msg.style.fontWeight = '600';
        msg.style.color = '#333';
        msg.textContent = 'Model in Development';
        modelBtn.parentElement.appendChild(msg);
      } else {
        // If already present, ensure it reads the exact message
        msg.textContent = 'Model in Development';
      }
    });
  }

  // README toggle: fetch and render ./data/external/fraud.md only
  if (readmeToggle && readmeContainer) {
    let loaded = false;
    readmeToggle.addEventListener('click', async () => {
      const open = readmeContainer.style.display !== 'none' && readmeContainer.style.display !== '';
      if (open) {
        // Hide
        readmeContainer.style.display = 'none';
        readmeToggle.textContent = 'Show Project README';
        return;
      }
      // Show
      readmeContainer.style.display = '';
      readmeToggle.textContent = 'Hide Project README';
      if (!loaded) {
        const url = './data/external/fraud.md';
        try {
          const resp = await fetch(url, { cache: 'no-cache' });
          if (!resp.ok) throw new Error('Not found');
          const md = await resp.text();
          if (window.marked && window.DOMPurify) {
            const html = window.marked.parse(md);
            readmeContainer.innerHTML = window.DOMPurify.sanitize(html);
          } else {
            readmeContainer.textContent = md;
          }
          loaded = true;
        } catch (err) {
          readmeContainer.innerHTML = '<p style="color:#b00"><em>Unable to load project README.</em></p>';
          console.error('Failed to load fraud.md:', err);
        }
      }
    });
  }
});
