#!/usr/bin/env python3
"""Generate profile stat cards (stats, top languages, streak) as SVG files.

Fetches public data for a user via the GitHub GraphQL API (GITHUB_TOKEN)
and renders light/dark variants into the output directory. Stdlib only.
"""
import argparse
import datetime as dt
import json
import os
import urllib.request

API = "https://api.github.com/graphql"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

PALETTES = {
    "": {"bg": "#ffffff", "border": "#d0d7de", "title": "#0969da",
         "text": "#24292f", "sub": "#57606a", "accent": "#0969da",
         "track": "#eaeef2"},
    "-dark": {"bg": "#0d1117", "border": "#30363d", "title": "#58a6ff",
              "text": "#c9d1d9", "sub": "#8b949e", "accent": "#58a6ff",
              "track": "#21262d"},
}

USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(
      contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]
    ) { totalCount }
    contributionsCollection { totalCommitContributions }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false,
                 first: 100) {
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

CALENDAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": "bearer " + os.environ["GITHUB_TOKEN"],
        "Content-Type": "application/json",
        "User-Agent": "profile-stats-generator",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def fetch_data(login):
    user = gql(USER_QUERY, {"login": login})["user"]

    langs = {}
    stars = 0
    for repo in user["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            color = edge["node"]["color"] or "#8b949e"
            size, _ = langs.get(name, (0, color))
            langs[name] = (size + edge["size"], color)

    created = dt.date.fromisoformat(user["createdAt"][:10])
    today = dt.date.today()
    counts = {}
    for year in range(created.year, today.year + 1):
        data = gql(CALENDAR_QUERY, {
            "login": login,
            "from": "%d-01-01T00:00:00Z" % year,
            "to": "%d-12-31T23:59:59Z" % year,
        })
        calendar = data["user"]["contributionsCollection"]["contributionCalendar"]
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                date = dt.date.fromisoformat(day["date"])
                if created <= date <= today:
                    counts[date] = day["contributionCount"]

    return {
        "login": login,
        "created": created,
        "today": today,
        "stars": stars,
        "commits_year": user["contributionsCollection"]["totalCommitContributions"],
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "langs": langs,
        "counts": counts,
    }


def compute_streaks(counts, today):
    total = sum(counts.values())
    longest = (0, None, None)
    run_start = None
    run_len = 0
    for date in sorted(counts):
        if counts[date] > 0:
            if run_len == 0:
                run_start = date
            run_len += 1
            if run_len > longest[0]:
                longest = (run_len, run_start, date)
        else:
            run_len = 0

    cur_end = today if counts.get(today, 0) > 0 else today - dt.timedelta(days=1)
    cur_len = 0
    date = cur_end
    while counts.get(date, 0) > 0:
        cur_len += 1
        date -= dt.timedelta(days=1)
    cur_start = cur_end - dt.timedelta(days=cur_len - 1) if cur_len else None
    current = (cur_len, cur_start, cur_end if cur_len else None)
    return total, current, longest


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def fmt_num(value):
    if value >= 100000:
        return "%.0fk" % (value / 1000)
    if value >= 10000:
        return "%.1fk" % (value / 1000)
    return "{:,}".format(value)


def fmt_date(date, today):
    if date is None:
        return ""
    label = "%s %d" % (MONTHS[date.month - 1], date.day)
    if date.year != today.year:
        label += ", %d" % date.year
    return label


def svg_open(width, height, palette):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" role="img">'
            '<rect x="0.5" y="0.5" width="%d" height="%d" rx="6" fill="%s" '
            'stroke="%s"/>' % (width, height, width, height,
                               width - 1, height - 1,
                               palette["bg"], palette["border"]))


def text(x, y, content, size, fill, weight="400", anchor="start"):
    return ('<text x="%s" y="%s" font-family="%s" font-size="%d" '
            'font-weight="%s" fill="%s" text-anchor="%s">%s</text>'
            % (x, y, FONT, size, weight, fill, anchor, content))


def star_points(cx, cy, outer, inner):
    import math
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = math.pi / 2 + i * math.pi / 5
        points.append("%.2f,%.2f" % (cx - radius * math.cos(angle),
                                     cy - radius * math.sin(angle)))
    return " ".join(points)


def icon(kind, x, y, color):
    group = '<g transform="translate(%d,%d)" stroke="%s" fill="none" stroke-width="1.6">' % (x, y, color)
    if kind == "star":
        return ('<polygon points="%s" fill="%s" stroke="none" '
                'transform="translate(%d,%d)"/>'
                % (star_points(8, 8.5, 7, 2.8), color, x, y))
    if kind == "commit":
        group += ('<circle cx="8" cy="8" r="3.4"/>'
                  '<line x1="0.5" y1="8" x2="4.6" y2="8"/>'
                  '<line x1="11.4" y1="8" x2="15.5" y2="8"/>')
    elif kind == "pr":
        group += ('<circle cx="3.5" cy="3.5" r="2.2"/>'
                  '<circle cx="3.5" cy="12.5" r="2.2"/>'
                  '<circle cx="12.5" cy="12.5" r="2.2"/>'
                  '<line x1="3.5" y1="5.7" x2="3.5" y2="10.3"/>'
                  '<path d="M7.5 3.5 h1.5 a3.5 3.5 0 0 1 3.5 3.5 v3.3"/>')
    elif kind == "issue":
        group += '<circle cx="8" cy="8" r="6.2"/>'
        group += '<circle cx="8" cy="8" r="1.7" fill="%s" stroke="none"/>' % color
    elif kind == "people":
        group += ('<circle cx="8" cy="5.5" r="3"/>'
                  '<path d="M2.5 14.5 a5.5 5 0 0 1 11 0"/>')
    elif kind == "repo":
        group += ('<rect x="2.5" y="1.5" width="11" height="13" rx="1.6"/>'
                  '<line x1="5.5" y1="11.5" x2="10.5" y2="11.5"/>')
    return group + "</g>"


def render_stats(data, palette):
    width, height = 390, 195
    rows = [
        ("star", "Total stars earned", data["stars"]),
        ("commit", "Commits (last year)", data["commits_year"]),
        ("pr", "Pull requests", data["prs"]),
        ("issue", "Issues", data["issues"]),
        ("people", "Followers", data["followers"]),
        ("repo", "Contributed to", data["contributed"]),
    ]
    parts = [svg_open(width, height, palette),
             text(25, 33, esc(data["login"]) + "'s GitHub Stats", 17,
                  palette["title"], "600")]
    y = 58
    for kind, label, value in rows:
        parts.append(icon(kind, 25, y - 12, palette["accent"]))
        parts.append(text(48, y, esc(label), 13, palette["text"]))
        parts.append(text(width - 25, y, fmt_num(value), 13, palette["text"],
                          "600", "end"))
        y += 23
    parts.append("</svg>")
    return "".join(parts)


def render_langs(data, palette):
    width, height = 320, 195
    total_all = sum(size for size, _ in data["langs"].values())
    ranked = sorted(data["langs"].items(), key=lambda kv: -kv[1][0])
    shown = ranked[:6]
    other = total_all - sum(size for _, (size, _) in shown)
    entries = [(name, size, color) for name, (size, color) in shown]
    if other > 0:
        entries.append(("Other", other, palette["sub"]))

    parts = [svg_open(width, height, palette),
             text(25, 33, "Most Used Languages", 17, palette["title"], "600")]
    bar_x, bar_y, bar_w, bar_h = 25, 50, width - 50, 9
    parts.append('<clipPath id="bar"><rect x="%d" y="%d" width="%d" '
                 'height="%d" rx="4.5"/></clipPath>' % (bar_x, bar_y, bar_w, bar_h))
    parts.append('<rect x="%d" y="%d" width="%d" height="%d" rx="4.5" '
                 'fill="%s"/>' % (bar_x, bar_y, bar_w, bar_h, palette["track"]))
    x = bar_x
    for name, size, color in entries:
        seg = bar_w * size / total_all if total_all else 0
        parts.append('<rect x="%.2f" y="%d" width="%.2f" height="%d" '
                     'fill="%s" clip-path="url(#bar)"/>'
                     % (x, bar_y, seg, bar_h, color))
        x += seg

    col_w = (width - 50) / 2
    for index, (name, size, color) in enumerate(entries):
        cx = 25 + (index % 2) * col_w
        cy = 82 + (index // 2) * 21
        pct = 100.0 * size / total_all if total_all else 0
        parts.append('<circle cx="%.1f" cy="%.1f" r="4.2" fill="%s"/>'
                     % (cx + 4, cy - 4, color))
        parts.append(text(cx + 15, cy, "%s %.1f%%" % (esc(name), pct), 12,
                          palette["text"]))
    parts.append("</svg>")
    return "".join(parts)


def render_streak(data, palette):
    width, height = 495, 195
    total, current, longest = compute_streaks(data["counts"], data["today"])
    today = data["today"]

    parts = [svg_open(width, height, palette)]
    for x in (165, 330):
        parts.append('<line x1="%d" y1="30" x2="%d" y2="165" stroke="%s"/>'
                     % (x, x, palette["border"]))

    def column(cx, big, big_size, label, sub, color, label_y=118):
        parts.append(text(cx, 92, esc(big), big_size, color, "700", "middle"))
        parts.append(text(cx, label_y, esc(label), 14, palette["text"], "600",
                          "middle"))
        parts.append(text(cx, label_y + 22, esc(sub), 11, palette["sub"],
                          "400", "middle"))

    column(82, fmt_num(total), 28, "Total Contributions",
           "%s - Present" % fmt_date(data["created"], today), palette["text"])

    cur_len, cur_start, cur_end = current
    parts.append('<circle cx="247" cy="84" r="41" fill="none" stroke="%s" '
                 'stroke-width="5"/>' % palette["accent"])
    parts.append(text(247, 94, fmt_num(cur_len), 26, palette["accent"], "700",
                      "middle"))
    parts.append(text(247, 148, "Current Streak", 14, palette["accent"], "600",
                      "middle"))
    sub = ("%s - %s" % (fmt_date(cur_start, today), fmt_date(cur_end, today))
           if cur_len else "No active streak")
    parts.append(text(247, 170, esc(sub), 11, palette["sub"], "400", "middle"))

    lon_len, lon_start, lon_end = longest
    sub = ("%s - %s" % (fmt_date(lon_start, today), fmt_date(lon_end, today))
           if lon_len else "")
    column(412, fmt_num(lon_len), 28, "Longest Streak", sub, palette["text"])

    parts.append("</svg>")
    return "".join(parts)


def render_all(data, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for suffix, palette in PALETTES.items():
        for name, renderer in (("stats", render_stats),
                               ("top-langs", render_langs),
                               ("streak", render_streak)):
            path = os.path.join(out_dir, "%s%s.svg" % (name, suffix))
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(renderer(data, palette))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="out")
    parser.add_argument("--login",
                        default=os.environ.get("USER_LOGIN", "Mysttic"))
    args = parser.parse_args()
    render_all(fetch_data(args.login), args.out)


if __name__ == "__main__":
    main()
