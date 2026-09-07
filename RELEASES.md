# Hooking a project up to this site

This repository plays two roles: it is the profile readme and it is where
people download my apps. The app code lives in private repositories; only
finished release files and the pages that show them land here.

This document describes what a project has to do for its releases to arrive
here on their own. Chatt is the worked example and has run this way since
0.6.1.

## How the whole thing runs

1. The project builds and publishes a release on its own side, as before. The
   full release history stays there.
2. Right after that a separate job copies the same files here, under a tag
   carrying the project prefix.
3. Once the copy succeeds it deletes the older releases of that project along
   with their tags. One version stands on the site: the newest.
4. The project page queries the API on every visit and fills itself in, so
   publishing a release needs no commit here.

## The contract

Three things are read by more than one program, so changing any of them breaks
something beyond the page itself.

### 1. A tag with the project prefix

```
chatt-v0.6.2
skaner-v2.0.1
```

The prefix is mandatory. `GET /releases/latest` returns the newest release in
the whole repository regardless of which app it belongs to, so without a prefix
Chatt would see the scanner's release as its own. Everything that reads
releases filters on this prefix and takes the first of the list.

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
inside the app, if the project has that feature.

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

Goes after the job that publishes the release on the project's own side. Four
values change per project: `PROJECT`, `SITE`, `NAME` and the file count in the
checking step. Chatt already runs an equivalent job under Polish names; there
is nothing to rename there.

```yaml
  site:
    name: Copy to the site
    needs: [version, release]
    if: needs.version.outputs.publishing == 'true'
    runs-on: ubuntu-latest
    env:
      HUB: Mysttic/Mysttic
      PROJECT: chatt
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
            | { grep -E "^$PROJECT-v" || true; } \
            | { grep -vxF "$HUB_TAG" || true; } \
            | while read -r old; do
                echo "Deleting $old"
                gh release delete "$old" --repo "$HUB" --cleanup-tag --yes
              done
          echo "$HUB_TAG stays on the site" >> "$GITHUB_STEP_SUMMARY"
```

The order matters: the new release is created before the old ones are deleted,
so the page is never empty, not even for a moment. The `^$PROJECT-v` filter
keeps the deletion from touching the other projects' releases.

## What to do here

A `<project>/` directory with its own `index.html` and images, laid out like
`chatt/`. Everything shared lives in `assets/`, so a project page is markup
plus one configuration block:

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

A new project also joins as a card in `index.html` at the root; the shape to
copy sits there as a comment.

## Updating from inside the app

If the app checks for new releases itself, it asks exactly what the page asks:

```
GET https://api.github.com/repos/Mysttic/Mysttic/releases?per_page=30
Accept: application/vnd.github+json
```

Then: drop `draft` and `prerelease`, keep the tags with the project prefix,
take the first one, and pick the file for your platform from `assets[]` by
name.

Three things are worth keeping in mind:

- **The `/releases/latest` address does not fit here.** It returns the newest
  release in the whole repository, so with two projects it starts lying.
- **The limit without authentication is 60 requests per hour per IP address.**
  Asking once a day fits inside that with room to spare.
- **Failure has to be quiet.** A timeout, no network and a changed response
  shape end in a log line, and the app carries on.

Changing the tag scheme or the file names breaks updates for people who already
have the app installed, and they find out only when it stops working. If
something here has to change, the version that reads the new scheme ships
first, and the scheme changes after that.

## Checklist

- [ ] `HUB_TOKEN` in the project repository's secrets;
- [ ] the `site` job in the release workflow, with `PROJECT`, `NAME` and `SITE`
      set;
- [ ] tags with the `<project>-v` prefix;
- [ ] file names carrying the version and the platform;
- [ ] a `<project>/` directory with the page, wired to `assets/style.css`,
      `assets/theme.js` and `assets/releases.js`, and one `initDownloads()`
      call;
- [ ] a project card in the root `index.html`;
- [ ] after the first release: the page shows the number and downloads the
      files, and the project's older releases are gone from the release list.
