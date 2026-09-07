/* Download buttons, filled from the releases of this repository.
 *
 * Every project page calls initDownloads() once with its tag prefix and the
 * suffixes of the files it ships. Nothing else here is per-project, so a new
 * project page is markup plus that one call.
 *
 * The page expects these ids:
 *   release-version, release-date   the version badge and its date
 *   download-<id>, size-<id>        one pair per entry in files[]
 *
 * On any failure, and there are two worth naming, every button turns into a
 * link to the releases page, so the page is never left without a way to
 * download: the API is unreachable, or the unauthenticated rate limit of 60
 * requests per hour per IP address is spent.
 */
const RELEASES_REPO = 'Mysttic/Mysttic';

function formatSize(bytes) {
  const mb = bytes / (1024 * 1024);
  return mb >= 1 ? mb.toFixed(1) + ' MB' : Math.round(bytes / 1024) + ' KB';
}

function versionFromTag(tag, prefix) {
  return tag.replace(new RegExp('^' + prefix), '').replace(/^v/, '');
}

/* Releases of every project live in one repository, so the prefix is what
   tells them apart. The API returns them newest first. */
async function latestRelease(prefix) {
  const url = `https://api.github.com/repos/${RELEASES_REPO}/releases?per_page=30`;
  const response = await fetch(url, { headers: { Accept: 'application/vnd.github+json' } });
  if (!response.ok) throw new Error('HTTP ' + response.status);
  const all = await response.json();
  const ours = all.filter(r =>
    !r.draft && !r.prerelease && r.tag_name.startsWith(prefix));
  if (!ours.length) throw new Error('no release with the ' + prefix + ' prefix');
  return ours[0];
}

function fill(release, config) {
  const version = document.getElementById('release-version');
  if (version) version.textContent = versionFromTag(release.tag_name, config.tagPrefix);

  const date = document.getElementById('release-date');
  if (date && release.published_at) {
    date.textContent = ' · ' + new Date(release.published_at).toLocaleDateString(
      'en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  for (const { id, match } of config.files) {
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

function fallback(config) {
  const version = document.getElementById('release-version');
  if (version) version.textContent = 'see GitHub';
  for (const { id } of config.files) {
    const button = document.getElementById('download-' + id);
    if (!button) continue;
    button.href = `https://github.com/${RELEASES_REPO}/releases`;
    button.removeAttribute('aria-disabled');
    button.textContent = 'Releases on GitHub';
  }
}

function initDownloads(config) {
  const run = () => latestRelease(config.tagPrefix)
    .then(release => fill(release, config))
    .catch(() => fallback(config));
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
}
