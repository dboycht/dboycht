"""
Generate a GitHub-style contribution heatmap SVG from public events API.
Output: charts/activity-heatmap.svg
"""
import json, urllib.request, datetime, sys, os

USERNAME = "dboycht"
WEEKS = 53  # one full year
CELL = 12
GAP = 3
MARGIN_X, MARGIN_Y = 40, 30
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]  # GitHub dark theme

def fetch_events(username):
    """Fetch up to 300 recent public events (API limit)."""
    url = f"https://api.github.com/users/{username}/events/public?per_page=300"
    req = urllib.request.Request(url, headers={"User-Agent": "dboycht-readme"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def build_heatmap(events):
    today = datetime.date.today()
    # Align to most recent Sunday
    end = today - datetime.timedelta(days=today.weekday() + 1)
    start = end - datetime.timedelta(weeks=WEEKS - 1)

    grid = {}
    for ev in events:
        day = ev["created_at"][:10]
        grid[day] = grid.get(day, 0) + 1

    max_count = max(grid.values()) if grid else 1
    cells = []
    for w in range(WEEKS):
        for d in range(7):
            date = start + datetime.timedelta(weeks=w, days=d)
            if date > today:
                continue
            key = date.isoformat()
            count = grid.get(key, 0)
            level = min(int(count / max(max_count / 4, 1)), 4) if count else 0
            x = MARGIN_X + w * (CELL + GAP)
            y = MARGIN_Y + d * (CELL + GAP)
            color = COLORS[level]
            cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"><title>{key}: {count} events</title></rect>')

    svg_w = MARGIN_X * 2 + WEEKS * (CELL + GAP)
    svg_h = MARGIN_Y * 2 + 7 * (CELL + GAP)
    days_label = "".join(
        f'<text x="8" y="{MARGIN_Y + d * (CELL + GAP) + CELL - 2}" font-size="10" fill="#8b949e">{lbl}</text>'
        for d, lbl in enumerate(["", "Mon", "", "Wed", "", "Fri", ""])
    )
    months = []
    prev_m = None
    for w in range(WEEKS):
        date = start + datetime.timedelta(weeks=w)
        m = date.strftime("%b")
        if m != prev_m:
            months.append(f'<text x="{MARGIN_X + w * (CELL + GAP)}" y="18" font-size="10" fill="#8b949e">{m}</text>')
            prev_m = m

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">
  <style>text {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif; }}</style>
  <rect width="{svg_w}" height="{svg_h}" rx="8" fill="#0d1117"/>
  <text x="{MARGIN_X}" y="18" font-size="13" font-weight="600" fill="#f0f6fc">Activity ({start.isoformat()} ~ {today.isoformat()})</text>
  {''.join(months)}
  {days_label}
  {''.join(cells)}
</svg>"""


if __name__ == "__main__":
    events = fetch_events(USERNAME)
    svg = build_heatmap(events)
    out = os.path.join(os.path.dirname(__file__), "..", "charts", "activity-heatmap.svg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {out} ({len(events)} events)")
