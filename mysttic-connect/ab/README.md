# Mysttic Connect side by side with Mirth Connect 4.5.2

The recordings and the presentation shown on [the Mysttic Connect page](../)
(section "Side by side with Mirth Connect 4.5.2"). Recorded on 16 October 2026 by a script that
drives both Administrators at the same time, feeds both engines the same messages and compares the
outputs with the rules of the automated A/B test; nothing is edited by hand.

| Side | Docker image |
|---|---|
| left | the official Mirth Connect 4.5.2 image, digest `sha256:4afa295cfe7c5ffd596efee69594157fea87202e33d66bb4a98a52db4598f836` |
| right | Mysttic Connect 1.2.1, `ghcr.io/mysttic/mysttic-connect:1.2.1`, digest `sha256:0df9fc7984437cf125a9c007845fb46398f23a0fff693cbc9d0214761318fb57` |

Mysttic Connect 1.3.0, the release on the page, runs the same engine: its changes are in the
Administrator, the Windows installer and the Server Manager, not in message processing.

| File | Length | Result of the comparison |
|---|---|---|
| `01-import-kanalu.mp4` | 1:29 | identical |
| `02-hl7-mllp-ack.mp4` | 1:20 | identical |
| `03-http-do-pliku.mp4` | 1:52 | identical; only the default `User-Agent` header carries the other name |
| `04-skrypt-javascript.mp4` | 1:48 | identical |
| `05-dashboard-i-wiadomosci.mp4` | 1:21 | identical; only the default `User-Agent` header carries the other name |
| `mysttic-connect-1.2.1-ab.pdf`, `.pptx` | 23 slides | the same cards and screenshots |

The clips are 1920x1080, H.264, captions in Polish, no sound. `<clip>.jpg` is a frame of the
recording (the poster on the page), `<clip>-result.jpg` its closing card. `SHA256SUMS` lists the
recordings and the presentation.

Mirth Connect is a trademark of its owner. Mysttic Connect is an independent project, not affiliated
with or endorsed by it. The left side of every recording shows the official Mirth Connect 4.5.2
Docker image unchanged; the names and logos visible there belong to their owners.
