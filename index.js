// Minimal protector-model script: model dev button only
document.addEventListener('DOMContentLoaded', () => {
  const modelBtn = document.getElementById('model-btn');

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
});
