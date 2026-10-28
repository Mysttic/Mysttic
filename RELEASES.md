# Hooking a project up to this site

This repository plays two roles: it is the profile readme and it is where
people download my apps. Every project's code lives in a private repository, so
none of them can hand anyone a download link; only finished release files and
the pages that show them land here.

This document describes what a project has to do for its releases to arrive
here on their own. Chatt is the worked example and has run this way since
0.6.1.

Projects and their tag prefixes:

| Project | Page | Tag prefix |
|---|---|---|
| Chatt | `chatt/` | `chatt-v` |
| Tibia Sounds Config | `tibia-sounds-config/` | `tibia-sounds-config-v` |
| Treningi | `mysttic-trainings/` | `mysttic-trainings-v` |
| Treningi, exercise database | `mysttic-trainings/` (a label, no tile) | `mysttic-trainings-baza-v` |
| YT → MP4 | `wtyczka-yt/` | `wtyczka-yt-v` |
| Mysttic Barcode Scanner | `mysttic-barcode-scanner/` | `mysttic-barcode-scanner-v` |
| FortiVPN 2 | `fortivpn2/` | `fortivpn2-v` |
| simple-rest | `simple-rest/` | `simple-rest-v` |
| simple-hl7 | `simple-hl7/` | `simple-hl7-v` |
| Mysttic Connect, server | `mysttic-connect/` (`#server`) | `mysttic-connect-v` |
| Mysttic Connect, Administrator Launcher | `mysttic-connect/` (`#launcher`) | `mysttic-connect-launcher-v` |
| Mysttic Connect, Server Manager | `mysttic-connect/` (`#manager`) | `mysttic-connect-manager-v` |

Mysttic Connect is one project whose three parts are released separately from
1.2.0 on, each with its own version number and its own prefix, all three on one
page. No prefix is the beginning of another: after `mysttic-connect-` comes `v`,
`l` or `m`.

Treningi releases its exercise database apart from the app from 1.1.0 on,
under a prefix of its own. The database number is a plain integer
(`mysttic-trainings-baza-v10`), not `X.Y.Z`, and only the app downloads it: the
page shows the number and the date under the app's version line, with no tile
and no button. After `mysttic-trainings-` comes `v` or `b`, so neither prefix
is the beginning of the other.

## How the whole thing runs

1. The project builds and publishes a release on its own side, as before. The
   full release history stays there.
2. Right after that a separate job copies the same files here, under a tag
   carrying the project prefix.
3. Once the copy succeeds it deletes the older releases with the same prefix
   along with their tags. One version per prefix stands on the site: the
   newest.
4. The project page queries the API on every visit and fills itself in, so
   publishing a release needs no commit here.

## The contract

Three things are read by more than one program, so changing any of them breaks
something beyond the page itself. A fourth, the signature of the checksums, is
optional and so far used by Mysttic Connect only.

### 1. A tag with the project prefix

```
chatt-v0.6.2
wtyczka-yt-v1.0.3
```

The prefix is mandatory. `GET /releases/latest` returns the newest release in
the whole repository regardless of which app it belongs to, so without a prefix
Chatt would see the extension's release as its own. Everything that reads
releases keeps the tags made of the prefix and a version right after it, and
takes the highest version, not the first of the list (see
[Updating from inside the app](#updating-from-inside-the-app)).

"Right after it" means a tag counts only when a digit follows the prefix. A
plain "starts with" would let a future `chatt-viewer-v1.0.0` pass for Chatt.

### 2. File names carrying the version and the platform

```
<project>-<version>-<platform>.<extension>
```

Chatt:

```
chatt-0.6.2-windows-instalator.exe
chatt-0.6.2-windows.zip
chatt-0.6.2-android.apk
```

The other three, whose names the copy keeps exactly as the project builds them:

```
tibia-sounds-config-1.7.0-win-x64-setup.exe
tibia-sounds-config-1.7.0-win-x64-portable.exe
tibia-sounds-config-1.7.0-win-x64.zip

mysttic-trainings-1.0.0-android.apk

mysttic-trainings-baza-10.zip
mysttic-trainings-baza-10.json

wtyczka-yt-1.1.0-windows-setup.exe
wtyczka-yt-1.1.0-windows.zip

mysttic-barcode-scanner-v2.0.1.zip
mysttic-barcode-scanner-v2.0.1.uf2
desktop-agent-v2.0.1-win-x64.exe
demo-app-v2.0.1-win-x64.zip

fortivpn2-2.7.0.zip

simple-rest-1.1.0-windows-amd64.exe
simple-rest-1.1.0-linux-amd64
simple-rest-1.1.0-linux-arm64
simple-rest-1.1.0-checksums.txt

simple-hl7-0.1.0-windows-amd64.exe
simple-hl7-0.1.0-linux-amd64
simple-hl7-0.1.0-checksums.txt

mysttic-connect-1.2.0-windows-x64-setup.exe
mysttic-connect-1.2.0-unix.tar.gz
mysttic-connect-1.2.0-windows.zip
mysttic-connect-1.2.0-checksums.txt
mysttic-connect-1.2.0-checksums.txt.sig

mysttic-connect-launcher-1.2.0-windows-x64.exe
mysttic-connect-launcher-1.2.0-macos-aarch64.zip
mysttic-connect-launcher-1.2.0-macos-x64.zip
mysttic-connect-launcher-1.2.0-linux-x64.tar.gz
mysttic-connect-launcher-1.2.0-checksums.txt
mysttic-connect-launcher-1.2.0-checksums.txt.sig

mysttic-connect-manager-1.2.0-windows-x64-update.exe
mysttic-connect-manager-1.2.0-unix.tar.gz
mysttic-connect-manager-1.2.0-checksums.txt
mysttic-connect-manager-1.2.0-checksums.txt.sig
```

simple-rest ships four files, one binary per system plus the checksums; all
four begin with the project name, so the copying job's plain `--pattern
"<project>-*"` covers them.
simple-hl7 follows the same scheme with three files: no ARM build, the rest
is identical.

Treningi's exercise database has no platform and two files: the package and
its manifest, which carries the number, the size and the SHA-256 of the
package and the lowest app version that reads it. The app reads the manifest
first, downloads the package only when the user asks, and checks it against
the manifest before using it.

Mysttic Connect ships three releases from 1.2.0 on, one per part, each with
the checksums of its own files and, once the project signs them, the signature
of those checksums ([below](#4-the-signature-of-the-checksums)):

- the server, `mysttic-connect-v`: the Windows installer and the two packages
  (about 260 MB each). `unix` covers Linux and macOS, one archive for both, as
  in the Mirth Connect releases it replaces;
- the Administrator Launcher, `mysttic-connect-launcher-v`: Windows, macOS on
  Apple silicon and on Intel, and Linux. The Windows file keeps the ending
  `-windows-x64.exe`, which the server's Web Dashboard looks for;
- the Server Manager, `mysttic-connect-manager-v`: an updater for a server
  installed with the Windows installer (`-windows-x64-update.exe`) and a
  `-unix.tar.gz` to unpack over any other installation. Both only update the
  Server Manager of an existing Mysttic Connect 1.2.0 or later; the Server
  Manager itself comes with the server.

Up to 1.1.1 the launcher came inside the server release, as
`mysttic-connect-<version>-launcher-<os>-<cpu>`, and the page falls back to
those names until the first `mysttic-connect-launcher-v` release is here.

The project's own releases have more files (the source code, an SBOM,
vulnerability reports, a `SHA256SUMS` of all of them), so each part's site job
downloads that part's files by their full names, together with its checksums
file and signature, checks them with `sha256sum -c` and copies those, rather
than `--pattern "<project>-*"`. The checksums file is made on the project side
with just the lines of those files, and the copy leaves it as it is, or the
signature would no longer match. The source code never comes here: the job's
last step deletes any it finds and fails.

Each of the scanner's four is copied with its `.sha256` beside it, eight files
in all. FortiVPN 2 is the plain case: one file, and since the project already
names it `fortivpn2-…`, the copying job's default `--pattern "<project>-*"`
covers it with `PROJECT: fortivpn2`. That is also why the page directory is
`fortivpn2/` and not the repository's `FortiVPN-2`: the prefix, the directory
and the file name should be one word, and the file name is the one already
published.

The scanner is the awkward one. Its package carries `-v` before the version, it
has no platform because a `.uf2` and a web page have none, and its other three
files are named after neither the project nor one scheme. Its page matches four
shapes separately, and the copying job downloads with eight patterns rather than
one `<project>-*`.

Two of those names are read by programs rather than people: the configurator's
update card fetches the `.uf2`, and the desktop agent's self-update fetches
`desktop-agent-v<version>-win-x64.exe` by a name it builds from the version.
Renaming either one breaks updates for everyone who already has that version,
and they find out only when it stops working.

The `$` ending every pattern on the page is load-bearing here for a second
reason: without it the package pattern would match `...zip.sha256` and the
firmware pattern `...uf2.sha256`, and a download button would hand someone a
64-character text file.

Whatever the page shows has to be in the copy, so the pattern the copying job
downloads with covers every one of those files. A project publishing something
alongside them, a `SHA256SUMS.txt` for instance, either copies that too or the
page stops mentioning it.

The page matches files by the end of the name, and so does the updater inside
the app. File names are a fixed part of the contract, not a detail of one
release. The Polish word in the installer name is part of it too: renaming it
to `installer` breaks the updater for everyone who already has the app
installed, so it only changes together with a release that reads the new name.

### 3. Release notes: the number and the page address

```
Chatt 0.6.2

https://mysttic.github.io/Mysttic/chatt/
```

That is all. Notes generated from pull request history point into a private
repository, so the reader gets a 404. The same text shows on the update card
inside the app, if the project has that feature. A page with several parts
adds the anchor of the part
(`https://mysttic.github.io/Mysttic/mysttic-connect/#launcher`), and Mysttic
Connect's server notes add one line naming the Server Manager and launcher
versions inside the set. Treningi's exercise database notes add, in Polish like
the app, what changed in the database and the lowest app version that reads
it.

### 4. The signature of the checksums

Optional, and so far only Mysttic Connect's. A project that signs does it in
its own release workflow, and the copy brings the signature here unchanged,
next to the file it signs:

```
mysttic-connect-launcher-1.2.0-checksums.txt
mysttic-connect-launcher-1.2.0-checksums.txt.sig
```

The checksums file is what `sha256sum` writes and nothing else: one line per
file of the release, `<64 lowercase hex>  <file name>` with two spaces, each
ending in a line feed. It does not list itself or the signature. The `.sig` is
two lines of ASCII, ending in line feeds:

```
keyid=<8 hex>
sig=<base64>
```

- `sig` is an ECDSA signature on the P-256 curve with SHA-256
  (`SHA256withECDSA`) over the exact bytes of the checksums file: the DER that
  `openssl dgst -sha256 -sign key.pem` writes, in base64 on one line;
- `keyid` is the first 8 hex digits, lower case, of the SHA-256 of the public
  key in DER
  (`openssl pkey -pubin -in public.pem -outform DER | sha256sum | cut -c1-8`),
  which tells the app which of its keys to try.

The app carries the public keys in two slots, `current` and `next`, so a new
key ships one release ahead of the first release it signs. The private key
lives only in the project's release secrets, never here. The site never needs
it: the copy signs nothing, and a copy that changed the checksums file would
break the signature, which is the point.

An app that checks the signature treats a missing `.sig`, a key it does not
carry and a signature that does not match the same way: it may still tell the
user about the update, and download the file and check it against the
checksums, but it never runs an installer by itself; the user does that.
Mysttic Connect releases without a signature until its key exists, and its
release step only warns then.

## What to do on the project side

### A secret with a credential

The default `GITHUB_TOKEN` only reaches the repository the workflow runs in, so
copying here needs a token of its own.

1. https://github.com/settings/personal-access-tokens, fine-grained token.
2. Owner `Mysttic`, access limited to the `Mysttic/Mysttic` repository.
3. Permission **Contents: Read and write**.
4. In the project repository: *Settings, Secrets and variables, Actions, New
   repository secret*, named `HUB_TOKEN`.

The token has an expiry date. When it runs out the job stops with a readable
error, and the release in the project repository stays where it is.

### The job in the release workflow

Goes after the job that publishes the release on the project's own side. Five
values change per project: `PROJECT`, `PREFIX` (which `HUB_TAG` repeats),
`NAME`, `SITE` and the file count in the checking step. Chatt already runs an
equivalent job under Polish names; there is nothing to rename there.

```yaml
  site:
    name: Copy to the site
    needs: [version, release]
    if: needs.version.outputs.publishing == 'true'
    runs-on: ubuntu-latest
    env:
      HUB: Mysttic/Mysttic
      PROJECT: chatt
      PREFIX: chatt-v
      NAME: Chatt
      SITE: https://mysttic.github.io/Mysttic/chatt/
      VERSION: ${{ needs.version.outputs.version }}
      TAG: ${{ needs.version.outputs.tag }}
      HUB_TAG: chatt-v${{ needs.version.outputs.version }}
    steps:
      - name: Credential for the site repository
        env:
          HUB_TOKEN: ${{ secrets.HUB_TOKEN }}
        run: |
          set -uo pipefail
          if [ -z "${HUB_TOKEN:-}" ]; then
            echo "::error::No HUB_TOKEN secret. Release $TAG was made, the copy to the site was not."
            echo "::error::Needs a personal token with Contents: read and write on $HUB."
            exit 1
          fi

      - name: Files from the release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          set -euo pipefail
          mkdir -p copy
          gh release download "$TAG" --repo "$GITHUB_REPOSITORY" \
            --dir copy --pattern "$PROJECT-*"
          ls -la copy
          if [ "$(ls -1 copy | wc -l)" -ne 3 ]; then
            echo "::error::Expected three files in release $TAG."
            exit 1
          fi

      - name: Release notes
        run: |
          set -euo pipefail
          {
            echo "$NAME $VERSION"
            echo
            echo "$SITE"
          } > notes.md
          cat notes.md

      - name: Release on the site
        env:
          GH_TOKEN: ${{ secrets.HUB_TOKEN }}
        run: |
          set -euo pipefail
          if gh release view "$HUB_TAG" --repo "$HUB" >/dev/null 2>&1; then
            gh release delete "$HUB_TAG" --repo "$HUB" --cleanup-tag --yes
          fi
          gh release create "$HUB_TAG" copy/* \
            --repo "$HUB" \
            --title "$NAME $VERSION" \
            --notes-file notes.md \
            --target master

      - name: The site keeps one version
        env:
          GH_TOKEN: ${{ secrets.HUB_TOKEN }}
        run: |
          set -euo pipefail
          gh release list --repo "$HUB" --limit 100 --json tagName -q '.[].tagName' \
            | { grep -E "^${PREFIX}[0-9]" || true; } \
            | { grep -vxF "$HUB_TAG" || true; } \
            | while read -r old; do
                echo "Deleting $old"
                gh release delete "$old" --repo "$HUB" --cleanup-tag --yes
              done
          echo "$HUB_TAG stays on the site" >> "$GITHUB_STEP_SUMMARY"
```

The order matters: the new release is created before the old ones are deleted,
so the page is never empty, not even for a moment. The `^${PREFIX}[0-9]`
filter keeps the deletion from touching the other projects' releases, and the
digit after the prefix keeps it off a project whose prefix merely begins with
this one: `chatt-v` alone would also match a later `chatt-viewer-v1.0.0`. A
project with several parts runs the job once per part, each with its own
`PREFIX` and `HUB_TAG`, and each part keeps one version of its own.

## What to do here

A `<project>/` directory with its own `index.html` and images, laid out like
`chatt/`. Everything shared lives in `assets/`, so a project page is markup plus
one configuration block:

```html
<link rel="stylesheet" href="../assets/style.css">
<script src="../assets/theme.js"></script>
```

`theme.js` goes in `<head>` without `defer`: it writes the stored theme onto
`<html>` before the first paint, which is what keeps an overridden page from
flashing the other theme. The header carries the button it drives:

```html
<button class="theme" type="button" data-theme-toggle hidden></button>
```

At the end of `<body>`, the download section is filled by the shared script:

```html
<script src="../assets/releases.js"></script>
<script>
initDownloads({
  tagPrefix: 'chatt-v',
  files: [
    { id: 'exe', match: /-windows-instalator\.exe$/ },
    { id: 'zip', match: /-windows\.zip$/ },
    { id: 'apk', match: /-android\.apk$/ }
  ]
});
</script>
```

That call is the only per-project JavaScript. It expects the ids
`release-version` and `release-date` on the version line, and a
`download-<id>` button next to a `size-<id>` line for every entry in `files`.
It always reads the releases of this repository; `tagPrefix` is what picks out
the project's own, and of those it shows the highest version.

A page with several parts, each under its own prefix, calls it once per part,
and the calls share one request to the API. Each call after the first names its
own version line with `ids`. Until a part has a release of its own here, it can
say what to show instead: a `fallback`, the prefix and file patterns of an
older release that still carries its files (used only while that release has
every one of them), or `notYet`, a short text for the size lines; its buttons
then stay off rather than point at a releases page without its files.

```html
<script>
initDownloads({ tagPrefix: 'mysttic-connect-v', files: [ /* the server */ ] });
initDownloads({
  tagPrefix: 'mysttic-connect-launcher-v',
  ids: { version: 'launcher-version', date: 'launcher-date' },
  files: [ { id: 'launcher-win', match: /^mysttic-connect-launcher-.*-windows-x64\.exe$/ } ],
  fallback: {
    tagPrefix: 'mysttic-connect-v',
    files: [ { id: 'launcher-win', match: /-launcher-windows-x64\.exe$/ } ]
  }
});
initDownloads({
  tagPrefix: 'mysttic-connect-manager-v',
  ids: { version: 'manager-version', date: 'manager-date' },
  notYet: 'Available from Mysttic Connect 1.2.0',
  files: [ { id: 'manager-win', match: /^mysttic-connect-manager-.*-windows-x64-update\.exe$/ } ]
});
</script>
```

A new project also joins as a card in `index.html` at the root; the shape to
copy sits there as a comment.

## Updating from inside the app

If the app checks for new releases itself, it reads the same list its page
reads:

```
GET https://api.github.com/repos/Mysttic/Mysttic/releases?per_page=100
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
User-Agent: <App>/<version>
```

No token, no identifier of the user or the computer, no query parameters
beyond `per_page`. One page of 100, the most the API returns at once, holds
every project's release with room to spare. Apps already out there that ask
for 30 keep working while the site holds fewer than 30 releases.

Then:

1. drop `draft` and `prerelease`;
2. keep the tags that are exactly the prefix followed by a bare `X.Y.Z`;
3. take the **highest version**, compared number by number, not the first
   one in the list. The list is not in the order of publication: it follows
   the date of the commit each tag points at, the same for every release
   copied here on top of one commit of this repository. And a job that failed
   halfway leaves an older release behind;
4. offer it only when it is higher than the running one (an app may refuse a
   new major version and send the user to the page instead);
5. pick the files it needs from `assets[]` by name, the checksums file too if
   the project publishes one, and only when every one of them has the `state`
   `uploaded`; a release whose files are still arriving counts as no update
   yet, quietly;
6. if the project publishes checksums, check the size against `assets[].size`
   and the SHA-256 against the checksums file before using a file, and if it
   signs them, check the [signature](#4-the-signature-of-the-checksums) first.

An app that downloads takes files only from
`https://github.com/Mysttic/Mysttic/releases/download/<tag>/` and follows
redirects only over HTTPS and only to `github.com`,
`objects.githubusercontent.com` and `release-assets.githubusercontent.com`.

**An app must not ask its own repository.** A private repository answers 404 to
everyone but its owner, so the check silently never finds an update, and the
owner is the one person who will never notice. Tibia Sounds Config and Treningi
both ask this repository, filtered by their prefix. YT → MP4 has no updater of
its own and its readme sends people to the project page. Mysttic Barcode Scanner
adds two readers of the same kind: the configurator's update card and the
desktop agent's self-update. FortiVPN 2's panel is a fourth: it asks once a day
and offers to install what it finds. From 1.2.0 Mysttic Connect's Administrator
Launcher and Server Manager are two more: the launcher looks for
`mysttic-connect-launcher-v`, and the Server Manager reads one response for
both `mysttic-connect-manager-v` and the server beside it, `mysttic-connect-v`.
Both ask at most once a day, the check can be turned off, and the server itself
never asks. From 1.1.0 Treningi likewise reads one response for both its app,
`mysttic-trainings-v`, and its exercise database, `mysttic-trainings-baza-v`,
whose tags carry a bare integer in place of `X.Y.Z`.

Three things are worth keeping in mind:

- **The `/releases/latest` address does not fit this repository.** It returns
  the newest release across the whole of it, so with two projects copied here it
  starts lying. In a repository holding one project it is fine.
- **The limit without authentication is 60 requests per hour per IP address.**
  Asking once a day fits inside that with room to spare.
- **Failure has to be quiet.** A timeout, no network and a changed response
  shape end in a log line, and the app carries on.

Changing the tag scheme or the file names breaks updates for people who already
have the app installed, and they find out only when it stops working. If
something here has to change, the version that reads the new scheme ships
first, and the scheme changes after that. The same goes for this site: the
page learned the three Mysttic Connect prefixes before the first release that
uses them, and the Treningi page the database prefix before the first
database release.

## Checklist

- [ ] `HUB_TOKEN` in the project repository's secrets;
- [ ] the `site` job in the release workflow, with `PROJECT`, `PREFIX`, `NAME`
      and `SITE` set;
- [ ] tags with the `<project>-v` prefix;
- [ ] file names carrying the version and the platform;
- [ ] a `<project>/` directory with the page, wired to `assets/style.css`,
      `assets/theme.js` and `assets/releases.js`, and one `initDownloads()`
      call per prefix;
- [ ] a project card in the root `index.html`;
- [ ] after the first release: the page shows the number and downloads the
      files, and the project's older releases are gone from the release list.
