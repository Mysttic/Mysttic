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

  /* The colour of the bars around the page: the status bar of the site
     installed on a phone (manifest.webmanifest), and the toolbar some browsers
     tint to match the page. It is the page background, read from style.css
     rather than repeated here, so this file comes after the stylesheet, as it
     does on every page. A theme-color tag with a media query in each page
     would follow the system, but not the override. */
  var bar = document.createElement('meta');
  bar.name = 'theme-color';
  document.head.appendChild(bar);

  function paintBar() {
    var bg = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
    if (bg) bar.content = bg;
  }

  function apply(mode) {
    var root = document.documentElement;
    if (mode === 'system') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', mode);
    paintBar();
  }

  var mode = stored();
  apply(mode);

  /* A page that follows the system changes with it while open, at dusk for
     instance. The stylesheet needs no help there; the bar has to be told. */
  var system = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
  if (system && system.addEventListener) system.addEventListener('change', paintBar);
  else if (system && system.addListener) system.addListener(paintBar); // Safari before 14

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
