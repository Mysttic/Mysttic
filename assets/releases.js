/* Download buttons, filled from the releases of this repository.
 *
 * Every project page calls initDownloads() with its tag prefix and the
 * suffixes of the files it ships. Nothing else here is per-project, so a new
 * project page is markup plus that one call.
 *
 * Every project's code repository is private, so none of them can hand anyone a
 * download link. Each one's workflow copies its release files here under a tag
 * carrying the project prefix, and that prefix is what tells them apart.
 *
 * The page expects these ids:
 *   release-version, release-date   the version badge and its date
 *   download-<id>, size-<id>        one pair per entry in files[]
 *
 * A page with several parts released on their own, each under its own prefix
 * (Mysttic Connect: the server, the Administrator Launcher and the Server
 * Manager), calls initDownloads() once per part, and the calls share one
 * request. A call for a second part names its own badge, and may say what to
 * show before that part has a release here:
 *   ids: { version, date }           the ids of its badge and date
 *   fallback: { tagPrefix, files }   an older release, under another prefix,
 *                                    that still carries the part's files, and
 *                                    their patterns there; used only while it
 *                                    carries every one of them
 *   notYet: '...'                    otherwise, a line for the size slots; the
 *                                    buttons stay off rather than send people
 *                                    to a releases page without the files
 *
 * On any failure, and there are two worth naming, every button turns into a
 * link to the releases page, so the page is never left without a way to
 * download: the API is unreachable, or the unauthenticated rate limit of 60
 * requests per hour per IP address is spent.
 */
const RELEASES_REPO = 'Mysttic/Mysttic';

function formatSize(bytes) {
  const mb = bytes / (1024 * 1024);
  return mb >= 1 ? mb.toFixed(1) + ' MB' : Math.max(1, Math.round(bytes / 1024)) + ' KB';
}

function versionFromTag(tag, prefix) {
  return tag.replace(new RegExp('^' + prefix), '').replace(/^v/, '');
}

/* One request per page however many times initDownloads() is called, so a page
   with three parts spends one of the sixty requests an hour, not three. A
   request that failed stays failed for the whole page. */
let releasesRequest = null;

function allReleases() {
  if (!releasesRequest) releasesRequest = fetchReleases();
  return releasesRequest;
}

async function fetchReleases() {
  const url = `https://api.github.com/repos/${RELEASES_REPO}/releases?per_page=100`;
  const response = await fetch(url, { headers: { Accept: 'application/vnd.github+json' } });
  if (!response.ok) throw new Error('HTTP ' + response.status);
  const all = await response.json();
  if (!Array.isArray(all)) throw new Error('not a list of releases');
  return all;
}

/* X.Y.Z as three numbers, or null for any other shape. */
function semver(version) {
  const m = /^(\d+)\.(\d+)\.(\d+)$/.exec(version);
  return m ? m.slice(1).map(Number) : null;
}

/* Every project's releases sit in this one repository, so the prefix is what
   tells them apart. A tag counts only when a digit follows the prefix, so that
   chatt-v would never pick up a chatt-viewer-v1.0.0.

   Normally a prefix has exactly one release here, the copying job having
   deleted the older ones, but a job that failed halfway leaves two behind.
   Rather than trust the order the API returns, take the highest version, as
   the apps that update themselves do; between tags that are not X.Y.Z, the one
   published last. Null when no release carries the prefix. */
function latestRelease(all, prefix) {
  const ours = all.filter(r =>
    r && !r.draft && !r.prerelease && typeof r.tag_name === 'string' &&
    r.tag_name.startsWith(prefix) && /^\d/.test(r.tag_name.slice(prefix.length)));
  if (!ours.length) return null;
  const when = r => Date.parse(r.published_at || r.created_at) || 0;
  const newer = (a, b) => {
    const va = semver(versionFromTag(a.tag_name, prefix));
    const vb = semver(versionFromTag(b.tag_name, prefix));
    const i = va && vb ? va.findIndex((n, k) => n !== vb[k]) : -1;
    return i >= 0 ? va[i] > vb[i] : when(a) > when(b);
  };
  return ours.reduce((best, r) => (newer(r, best) ? r : best));
}

/* The badge this call fills: the page's only one, or the pair named in ids. */
function badge(config) {
  const ids = config.ids || { version: 'release-version', date: 'release-date' };
  const byId = id => (id ? document.getElementById(id) : null);
  return { version: byId(ids.version), date: byId(ids.date) };
}

function fill(release, prefix, files, config) {
  const { version, date } = badge(config);
  if (version) version.textContent = versionFromTag(release.tag_name, prefix);
  if (date && release.published_at) {
    date.textContent = ' · ' + new Date(release.published_at).toLocaleDateString(
      'en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  for (const { id, match } of files) {
    const asset = (release.assets || []).find(a => match.test(a.name));
    const button = document.getElementById('download-' + id);
    const size = document.getElementById('size-' + id);
    if (!button || !size) continue;
    if (!asset) { size.textContent = 'Not in this release'; continue; }
    button.href = asset.browser_download_url;
    button.removeAttribute('aria-disabled');
    size.textContent = asset.name + ' · ' + formatSize(asset.size);
  }
}

/* A part announced before its first release: the buttons stay off and the
   size lines say when the files come. */
function notYetReleased(config) {
  const { version } = badge(config);
  if (version) version.textContent = 'not released yet';
  for (const { id } of config.files) {
    const size = document.getElementById('size-' + id);
    if (size) size.textContent = config.notYet;
  }
}

function linkToReleasesPage(config) {
  const { version } = badge(config);
  if (version) version.textContent = 'see GitHub';
  const ids = new Set(config.files.map(f => f.id));
  if (config.fallback) config.fallback.files.forEach(f => ids.add(f.id));
  for (const id of ids) {
    const button = document.getElementById('download-' + id);
    if (!button) continue;
    button.href = `https://github.com/${RELEASES_REPO}/releases`;
    button.removeAttribute('aria-disabled');
    button.textContent = 'Releases on GitHub';
  }
}

function show(all, config) {
  const own = latestRelease(all, config.tagPrefix);
  if (own) return fill(own, config.tagPrefix, config.files, config);

  const fb = config.fallback;
  const old = fb && latestRelease(all, fb.tagPrefix);
  const carriesAll = old && fb.files.every(({ match }) =>
    (old.assets || []).some(a => match.test(a.name)));
  if (carriesAll) return fill(old, fb.tagPrefix, fb.files, config);
  if (config.notYet) return notYetReleased(config);
  throw new Error('no release with the ' + config.tagPrefix + ' prefix');
}

function initDownloads(config) {
  const run = () => allReleases()
    .then(all => show(all, config))
    .catch(() => linkToReleasesPage(config));
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
}
