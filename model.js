document.addEventListener('DOMContentLoaded', () => {
  console.log('Protector model page loaded.');
  const iframe = document.querySelector('iframe');
  // Fallback hint if the embed fails to load in 3s
  setTimeout(() => {
    try {
      const sameDoc = iframe.contentDocument; // may throw cross-origin; ignore
    } catch (e) {
      const wrap = document.querySelector('.framewrap');
      const hint = document.createElement('p');
      hint.className = 'subtle';
      hint.style.margin = '0.5rem 0 0.75rem';
      hint.textContent = 'If the embed is blocked by your browser, use the “Open Power BI Report” button above.';
      wrap.prepend(hint);
    }
  }, 3000);
});
