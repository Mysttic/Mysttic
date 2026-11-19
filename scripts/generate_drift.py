#!/usr/bin/env python3
"""Render the last year's contribution graph as an animated drift card.

A car drifts across the grid and paints every day with the colour of its
real contribution level; days without contributions stay dark. Fetches the
same calendar the profile shows (GitHub GraphQL, GITHUB_TOKEN) and writes
light/dark SVG variants animated with SMIL, so they play inside an <img>.
Stdlib only.
"""
import argparse
import datetime as dt
import math
import os
import random

from generate_stats import FONT, MONTHS, esc, gql

CALENDAR_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date weekday contributionCount contributionLevel }
        }
      }
    }
  }
}
"""

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

THEMES = {
    "": {"bg": "#ffffff", "border": "#d0d7de", "empty": "#ebedf0",
         "text": "#57606a",
         "levels": ["#cdb8f6", "#a855f7", "#ec4899", "#f97316"],
         "smoke": "#9198a1", "smoke_op": 0.45,
         "skid": "#24292f", "skid_op": 0.2, "shadow_op": 0.22},
    "-dark": {"bg": "#100c1a", "border": "#30363d", "empty": "#1e1829",
              "text": "#8b949e",
              "levels": ["#6527d6", "#b437f2", "#f42a94", "#f7973a"],
              "smoke": "#ece8f5", "smoke_op": 0.55,
              "skid": "#000000", "skid_op": 0.6, "shadow_op": 0.55},
}

# Layout (px) and timeline (s).
PITCH, CELL = 14, 11
LEFT, TOP, BOTTOM = 36, 58, 62
LOOP = 16.0                # one full cycle
BURNOUT, DRIVE_START, DRIVE = 0.3, 0.9, 11.0
FADE_START, FADE = 14.3, 0.9
CAR_SCALE = 1.25
FPS = 30
SIM_DT = 1.0 / 120


def fetch_calendar(login):
    data = gql(CALENDAR_QUERY, {"login": login})
    calendar = data["user"]["contributionsCollection"]["contributionCalendar"]
    days = []
    for week_index, week in enumerate(calendar["weeks"]):
        for day in week["contributionDays"]:
            days.append({
                "week": week_index,
                "weekday": day["weekday"],
                "date": dt.date.fromisoformat(day["date"]),
                "count": day["contributionCount"],
                "level": LEVELS.get(day["contributionLevel"], 0),
            })
    return {"total": calendar["totalContributions"],
            "weeks": len(calendar["weeks"]), "days": days}


# --- the car's route -------------------------------------------------------

def catmull_rom(points, steps=24):
    """Centripetal Catmull-Rom through all points, as a dense polyline."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]

        def knot(t, a, b):
            return t + max(math.dist(a, b), 1e-6) ** 0.5

        t0 = 0.0
        t1 = knot(t0, p0, p1)
        t2 = knot(t1, p1, p2)
        t3 = knot(t2, p2, p3)
        for step in range(steps):
            t = t1 + (t2 - t1) * step / steps
            a1 = lerp(p0, p1, (t - t0) / (t1 - t0))
            a2 = lerp(p1, p2, (t - t1) / (t2 - t1))
            a3 = lerp(p2, p3, (t - t2) / (t3 - t2))
            b1 = lerp(a1, a2, (t - t0) / (t2 - t0))
            b2 = lerp(a2, a3, (t - t1) / (t3 - t1))
            out.append(lerp(b1, b2, (t - t1) / (t2 - t1)))
    out.append(points[-1])
    return out


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def loop_points(cx, cy, radius, start_deg, sweep_deg, count=12):
    return [(cx + radius * math.cos(math.radians(start_deg + sweep_deg * k / count)),
             cy + radius * math.sin(math.radians(start_deg + sweep_deg * k / count)))
            for k in range(1, count)]


def route(grid_x, grid_w, mid_y, half_h):
    """Waypoints: a launch, an S, a donut above, a swerve, a donut below."""
    def at(fx, fy):
        return (grid_x + grid_w * fx, mid_y + half_h * fy)

    radius = 0.8 * half_h
    up = at(0.40, -0.75)       # centre of the donut above the grid
    down = at(0.66, 0.75)      # centre of the donut below it
    pts = [(grid_x + 26, mid_y), at(0.09, 0.05), at(0.16, 0.45),
           at(0.23, 0.6), at(0.31, 0.25)]
    pts.append((up[0], up[1] + radius))
    pts += loop_points(up[0], up[1], radius, 90, -360)     # anticlockwise
    pts.append((up[0], up[1] + radius))
    pts += [at(0.49, 0.2), at(0.56, -0.15)]
    pts.append((down[0], down[1] - radius))
    pts += loop_points(down[0], down[1], radius, -90, 360)  # clockwise
    pts.append((down[0], down[1] - radius))
    pts += [at(0.76, -0.25), at(0.84, 0.25), at(0.92, 0.0), at(1.0, 0.0),
            (grid_x + grid_w + 90, mid_y)]
    return catmull_rom(pts)


def drive(polyline):
    """Simulate the run: position, heading and slip angle every SIM_DT."""
    cum = [0.0]
    for a, b in zip(polyline, polyline[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    length = cum[-1]

    def sample(s):
        s = min(max(s, 0.0), length)
        lo, hi = 0, len(cum) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if cum[mid] <= s:
                lo = mid
            else:
                hi = mid
        seg = cum[hi] - cum[lo] or 1.0
        return lerp(polyline[lo], polyline[hi], (s - cum[lo]) / seg)

    ramp = 0.7                       # launch: full speed after this long
    v_max = length / (DRIVE - ramp / 2)
    frames, s, t = [], 0.0, 0.0
    heading_prev, slip = None, 0.0
    while t <= DRIVE + 1e-9:
        x, y = sample(s)
        ax, ay = sample(s - 4)
        bx, by = sample(s + 4)
        course = math.atan2(by - ay, bx - ax)
        if heading_prev is not None:
            while course - heading_prev > math.pi:
                course -= 2 * math.pi
            while course - heading_prev < -math.pi:
                course += 2 * math.pi
        cx_, cy_ = sample(s - 14)
        dx_, dy_ = sample(s + 14)
        turn = math.atan2(dy_ - y, dx_ - x) - math.atan2(y - cy_, x - cx_)
        turn = (turn + math.pi) % (2 * math.pi) - math.pi
        target = max(-0.95, min(0.95, turn * 1.6))       # nose into the turn
        slip += (target - slip) * (1 - math.exp(-SIM_DT / 0.14))
        frames.append({"t": DRIVE_START + t, "x": x, "y": y,
                       "course": course, "slip": slip})
        heading_prev = course
        speed = v_max * min(1.0, t / ramp)
        s += speed * SIM_DT
        t += SIM_DT
    return frames


def rotate(vx, vy, angle):
    c, s = math.cos(angle), math.sin(angle)
    return vx * c - vy * s, vx * s + vy * c


# --- SVG -------------------------------------------------------------------

def frac(seconds):
    return min(max(seconds / LOOP, 0.0), 1.0)


def key_times(times):
    """keyTimes must rise strictly; nudge ties apart."""
    out, last = [], -1.0
    for value in times:
        value = max(frac(value), last + 0.0001) if last >= 0 else frac(value)
        out.append(value)
        last = value
    out[-1] = 1.0
    return ";".join("%.4f" % v for v in out)


def animate(attr, values, times, extra=""):
    return ('<animate attributeName="%s" values="%s" keyTimes="%s" dur="%gs" '
            'repeatCount="indefinite"%s/>'
            % (attr, ";".join(str(v) for v in values), key_times(times), LOOP,
               extra))


def mix(color, other, amount):
    a = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * amount)
                                   for x, y in zip(a, b))


CAR = """
<ellipse cx="2" cy="3" rx="29" ry="15" fill="#000" opacity="{shadow}" filter="url(#soft)"/>
<rect x="-20" y="-14" width="10" height="5" rx="1.5" fill="#0b0d12"/>
<rect x="-20" y="9" width="10" height="5" rx="1.5" fill="#0b0d12"/>
<rect x="11" y="-13.5" width="9" height="4.5" rx="1.5" fill="#0b0d12"/>
<rect x="11" y="9" width="9" height="4.5" rx="1.5" fill="#0b0d12"/>
<path d="M-25 -8 Q-25 -12 -20 -12 L13 -12 Q23 -11 26 -4 L26 4 Q23 11 13 12 L-20 12 Q-25 12 -25 8 Z" fill="url(#paint)"/>
<rect x="-25" y="-10.5" width="3.2" height="21" rx="1.2" fill="#163f99"/>
<path d="M12 -5 L24 -3.5 M12 5 L24 3.5" stroke="#9fd0ff" stroke-width="0.9" opacity="0.55"/>
<path d="M-13 -8.5 L6 -8.5 Q11 -8 12 -4 L12 4 Q11 8 6 8.5 L-13 8.5 Q-16 8.5 -16 5 L-16 -5 Q-16 -8.5 -13 -8.5 Z" fill="#0a1120"/>
<rect x="-10" y="-6" width="13" height="12" rx="3" fill="#4f9ef6"/>
<rect x="-8" y="-4.5" width="9" height="9" rx="2" fill="#73b6ff" opacity="0.6"/>
<ellipse cx="6" cy="-13" rx="2.2" ry="1.4" fill="#2a6fd6"/>
<ellipse cx="6" cy="13" rx="2.2" ry="1.4" fill="#2a6fd6"/>
<ellipse cx="24.2" cy="-6.6" rx="1.3" ry="2.6" fill="#f4fbff"/>
<ellipse cx="24.2" cy="6.6" rx="1.3" ry="2.6" fill="#f4fbff"/>
<rect x="-25.6" y="-10" width="1.8" height="4.5" rx="0.8" fill="#ff3b4e"/>
<rect x="-25.6" y="5.5" width="1.8" height="4.5" rx="0.8" fill="#ff3b4e"/>
"""


def render_drift(calendar, theme, seed=7):
    rng = random.Random(seed)
    weeks = calendar["weeks"]
    grid_w = weeks * PITCH - (PITCH - CELL)
    grid_h = 7 * PITCH - (PITCH - CELL)
    width = LEFT * 2 + grid_w
    height = TOP + grid_h + BOTTOM
    mid_y = TOP + grid_h / 2

    frames = drive(route(LEFT, grid_w, mid_y, grid_h / 2))
    drive_end = frames[-1]["t"]
    total = calendar["total"]
    label = "%s contributions in the last year" % "{:,}".format(total)

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d" role="img" aria-label="%s">'
             % (width, height, width, height, esc(label)),
             "<title>%s</title>" % esc(label),
             '<defs>'
             '<linearGradient id="paint" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="#5aa9ff"/>'
             '<stop offset="0.5" stop-color="#2f7be8"/>'
             '<stop offset="1" stop-color="#1b55bd"/></linearGradient>'
             '<filter id="smoke" x="-20%%" y="-50%%" width="140%%" height="200%%">'
             '<feGaussianBlur stdDeviation="5"/></filter>'
             '<filter id="soft" x="-30%%" y="-60%%" width="160%%" height="220%%">'
             '<feGaussianBlur stdDeviation="2.5"/></filter>'
             '<clipPath id="card"><rect width="%d" height="%d" rx="6"/></clipPath>'
             '</defs>' % (width, height),
             '<rect x="0.5" y="0.5" width="%d" height="%d" rx="6" fill="%s" '
             'stroke="%s"/>' % (width - 1, height - 1, theme["bg"],
                                theme["border"]),
             '<g clip-path="url(#card)">']

    # Month labels over the first column of each month.
    first_of_week = {}
    for day in calendar["days"]:
        first_of_week.setdefault(day["week"], day["date"])
    last_label = -10
    for week in range(weeks):
        date = first_of_week.get(week)
        if date is None or week == 0:
            continue
        if date.day <= 7 and week - last_label >= 3 and week < weeks - 1:
            parts.append('<text x="%d" y="%d" font-family="%s" font-size="10" '
                         'fill="%s">%s</text>'
                         % (LEFT + week * PITCH, TOP - 8, FONT, theme["text"],
                            MONTHS[date.month - 1]))
            last_label = week

    # Cells: each real level is painted the first time the car reaches it.
    parts.append("<g>")
    for day in calendar["days"]:
        x = LEFT + day["week"] * PITCH
        y = TOP + day["weekday"] * PITCH
        level = day["level"]
        cell = ('<rect x="%d" y="%d" width="%d" height="%d" rx="2.5" fill="%s"'
                % (x, y, CELL, CELL,
                   theme["levels"][level - 1] if level else theme["empty"]))
        if not level:
            parts.append(cell + "/>")
            continue
        cx, cy = x + CELL / 2, y + CELL / 2
        painted = drive_end
        for frame in frames:
            if frame["x"] >= cx - 6 or math.hypot(frame["x"] - cx,
                                                  frame["y"] - cy) < 24:
                painted = frame["t"]
                break
        color = theme["levels"][level - 1]
        fade = FADE_START + 0.6 * day["week"] / weeks
        parts.append(cell + ">" + animate(
            "fill",
            [theme["empty"], theme["empty"], mix(color, "#ffffff", 0.65),
             color, color, theme["empty"], theme["empty"]],
            [0, painted, painted + 0.07, painted + 0.45, fade, fade + FADE,
             LOOP]) + "</rect>")
    parts.append("</g>")

    # Skid marks under the rear wheels while the car is sliding.
    def runs(threshold):
        current = []
        for frame in frames:
            if abs(frame["slip"]) > threshold:
                current.append(frame)
            elif current:
                yield current
                current = []
        if current:
            yield current

    parts.append('<g fill="none" stroke="%s" stroke-width="2.4" '
                 'stroke-linecap="round" stroke-linejoin="round" opacity="%s">'
                 % (theme["skid"], theme["skid_op"]))
    for run in runs(0.3):
        if len(run) < 8:
            continue
        for side in (-9.5, 9.5):
            pts = []
            for frame in run[::2]:
                heading = frame["course"] + frame["slip"]
                ox, oy = rotate(-15 * CAR_SCALE, side * CAR_SCALE, heading)
                pts.append((frame["x"] + ox, frame["y"] + oy))
            length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:])) + 1
            d = "M" + " L".join("%.1f %.1f" % p for p in pts)
            parts.append(
                '<path d="%s" stroke-dasharray="%.1f %.1f" '
                'stroke-dashoffset="%.1f">' % (d, length, length, length)
                + animate("stroke-dashoffset", ["%.1f" % length, "%.1f" % length,
                                                0, 0],
                          [0, run[0]["t"], run[-1]["t"], LOOP])
                + animate("opacity", [1, 1, 0, 0],
                          [0, FADE_START, FADE_START + FADE, LOOP])
                + "</path>")
    parts.append("</g>")

    # Tyre smoke: puffs left behind while sliding, plus the launch burnout.
    parts.append('<g fill="%s" filter="url(#smoke)">' % theme["smoke"])
    burnout = [dict(frames[0], t=BURNOUT + k * 0.05)
               for k in range(int((DRIVE_START - BURNOUT) / 0.05))]
    next_puff = 0.0
    for frame in burnout + frames:
        t = frame["t"]
        slide = abs(frame["slip"])
        launch = t < DRIVE_START + 0.35
        if t < next_puff or not (launch or slide > 0.38):
            continue
        next_puff = t + 0.045
        heading = frame["course"] + frame["slip"]
        ox, oy = rotate(-26 + rng.uniform(-4, 4), rng.uniform(-10, 10), heading)
        px, py = frame["x"] + ox, frame["y"] + oy
        strength = 1.0 if launch else min(1.0, slide / 0.7)
        peak = theme["smoke_op"] * strength
        life = 1.1 + 0.7 * strength
        grow = 13 + 13 * strength
        drift_x, drift_y = rotate(-14, rng.uniform(-10, 10), heading)
        parts.append(
            '<circle cx="%.1f" cy="%.1f" r="3" opacity="0">' % (px, py)
            + animate("opacity", [0, 0, "%.2f" % peak, 0, 0],
                      [0, t, t + 0.12, t + life, LOOP])
            + animate("r", [3, 3, "%.1f" % grow, "%.1f" % grow],
                      [0, t, t + life, LOOP])
            + animate("cx", ["%.1f" % px, "%.1f" % px,
                             "%.1f" % (px + drift_x), "%.1f" % (px + drift_x)],
                      [0, t, t + life, LOOP])
            + animate("cy", ["%.1f" % py, "%.1f" % py,
                             "%.1f" % (py + drift_y), "%.1f" % (py + drift_y)],
                      [0, t, t + life, LOOP])
            + "</circle>")
    parts.append("</g>")

    # The car: translate and heading (course + slip) every 1/FPS s.
    step = max(1, round(1 / (FPS * SIM_DT)))
    keys = frames[::step]
    if keys[-1] is not frames[-1]:
        keys.append(frames[-1])
    start, end = keys[0], keys[-1]
    moves = (["%.1f %.1f" % (start["x"], start["y"])]
             + ["%.1f %.1f" % (f["x"], f["y"]) for f in keys]
             + ["%.1f %.1f" % (end["x"], end["y"])])
    angles = [math.degrees(f["course"] + f["slip"]) for f in keys]
    angles = ["%.1f" % angles[0]] + ["%.1f" % a for a in angles] + ["%.1f" % angles[-1]]
    times = [0] + [f["t"] for f in keys] + [LOOP]
    parts.append(
        '<g transform="translate(%.1f %.1f)">' % (start["x"], start["y"])
        + '<animateTransform attributeName="transform" type="translate" '
          'values="%s" keyTimes="%s" dur="%gs" repeatCount="indefinite"/>'
          % (";".join(moves), key_times(times), LOOP)
        + '<g transform="scale(%g)">' % CAR_SCALE
        + '<animateTransform attributeName="transform" type="rotate" '
          'values="%s" keyTimes="%s" dur="%gs" repeatCount="indefinite" '
          'additive="sum"/>' % (";".join(angles), key_times(times), LOOP)
        + CAR.format(shadow=theme["shadow_op"]).replace("\n", "")
        + "</g></g>")

    # Footer: the year's total and the legend.
    foot_y = height - 16
    parts.append('<text x="%d" y="%d" font-family="%s" font-size="12" '
                 'fill="%s">%s</text>'
                 % (LEFT, foot_y, FONT, theme["text"], esc(label)))
    legend_x = LEFT + grid_w - 5 * PITCH - 30
    parts.append('<text x="%d" y="%d" font-family="%s" font-size="11" '
                 'fill="%s" text-anchor="end">Less</text>'
                 % (legend_x - 6, foot_y, FONT, theme["text"]))
    for index, color in enumerate([theme["empty"]] + theme["levels"]):
        parts.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2.5" '
                     'fill="%s"/>' % (legend_x + index * PITCH, foot_y - 10,
                                      CELL, CELL, color))
    parts.append('<text x="%d" y="%d" font-family="%s" font-size="11" '
                 'fill="%s">More</text>'
                 % (legend_x + 5 * PITCH + 3, foot_y, FONT, theme["text"]))

    parts.append("</g></svg>")
    return "".join(parts)


def render_all(calendar, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for suffix, theme in THEMES.items():
        path = os.path.join(out_dir, "contrib-drift%s.svg" % suffix)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(render_drift(calendar, theme))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="out")
    parser.add_argument("--login",
                        default=os.environ.get("USER_LOGIN", "Mysttic"))
    args = parser.parse_args()
    render_all(fetch_calendar(args.login), args.out)


if __name__ == "__main__":
    main()
