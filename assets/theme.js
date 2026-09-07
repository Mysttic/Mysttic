/* Light and dark theme.
 *
 * The page follows the operating system setting on its own; the toggle in the
 * header only exists to override it, and the override is remembered per
 * browser. Load this file synchronously from <head>: it writes data-theme on
 * <html> before the first paint, so an overridden page never flashes the
 * other theme.
 */
(function () {
  var KEY = 'mysttic-theme';
  var MODES = ['system', 'light', 'dark'];
  var LABEL = { system: 'Auto', light: 'Light', dark: 'Dark' };
  var TITLE = {
    system: 'Theme follows your system, click for light',
    light: 'Light theme, click for dark',
    dark: 'Dark theme, click to follow your system'
  };

  function stored() {
    try {
      var saved = localStorage.getItem(KEY);
      return MODES.indexOf(saved) > -1 ? saved : 'system';
    } catch (e) {
      return 'system'; // private mode, or site data blocked
    }
  }

  function apply(mode) {
    var root = document.documentElement;
    if (mode === 'system') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', mode);
  }

  var mode = stored();
  apply(mode);

  document.addEventListener('DOMContentLoaded', function () {
    var button = document.querySelector('[data-theme-toggle]');
    if (!button) return;

    function paint() {
      button.textContent = LABEL[mode];
      button.title = TITLE[mode];
      button.setAttribute('aria-label', TITLE[mode]);
    }

    paint();
    button.hidden = false; // the markup hides it, so no dead button without JS

    button.addEventListener('click', function () {
      mode = MODES[(MODES.indexOf(mode) + 1) % MODES.length];
      try { localStorage.setItem(KEY, mode); } catch (e) { /* nothing to do */ }
      apply(mode);
      paint();
    });
  });
})();
