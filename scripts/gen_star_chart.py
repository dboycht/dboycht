"""
Generate a star chart SVG from the GitHub API.

Only repositories that actually have stars are drawn (MIN_STARS = 1);
zero-star repos are filtered out, so the chart never shows empty bars.

Output: charts/star-chart.svg
Run:    python scripts/gen_star_chart.py      (also run daily by update-charts.yml)
"""
import json, urllib.request, os

USERNAME = "dboycht"
MIN_STARS = 1

# Repos to keep off the chart (2026-09-16 user choice: localization / old
# chemistry helpers / campus errand-running build are intentionally hidden).
EXCLUDE = {
    "ComplementaryShadersChinese",
    "XaerosWorldMapChinese",
    "Cheq",
    "Cheq-foreign-pu",
    "TPW",
}

SVG_W = 480
BAR_MAX_W = 250
BAR_H = 16
GAP = 10
MARGIN_X = 20
MARGIN_Y = 60
LABEL_W = 130          # width reserved for the repo name column
BAR_X = MARGIN_X + LABEL_W

LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Rust": "#dea584", "C#": "#178600", "HTML": "#e34c26", "CSS": "#563d7c",
    "PowerShell": "#012456", "Jupyter Notebook": "#DA5B0B", "Vue": "#4FC08D",
    "GDScript": "#355570", "Kotlin": "#A97BFF", "Java": "#b07219",
}


def fetch_repos(username):
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=stars&direction=desc"
    req = urllib.request.Request(url, headers={"User-Agent": "dboycht-readme"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def lang_color(lang):
    return LANG_COLORS.get(lang, "#8b949e")


def short_name(name, limit=19):
    return name if len(name) <= limit else name[: limit - 1] + "…"


def build_chart(repos):
    starred = [
        r for r in repos
        if r["stargazers_count"] >= MIN_STARS
        and not r["fork"]
        and r["name"] not in EXCLUDE
    ]
    starred.sort(key=lambda r: (-r["stargazers_count"], r["name"]))

    total_stars = sum(r["stargazers_count"] for r in starred)
    max_stars = max((r["stargazers_count"] for r in starred), default=1)

    rows = []
    for i, r in enumerate(starred):
        y = MARGIN_Y + i * (BAR_H + GAP)
        stars = r["stargazers_count"]
        w = max(round(stars / max_stars * BAR_MAX_W), 6)
        rows.append(
            f'  <text x="{MARGIN_X}" y="{y + 12}" class="label">{short_name(r["name"])}</text>\n'
            f'  <rect x="{BAR_X}" y="{y}" width="{w}" height="{BAR_H}" rx="3" fill="{lang_color(r.get("language"))}"/>\n'
            f'  <text x="{BAR_X + w + 6}" y="{y + 12}" class="count">{stars}</text>'
        )

    body = "\n".join(rows) if rows else (
        f'  <text x="{MARGIN_X}" y="{MARGIN_Y + 12}" class="count">no starred repositories yet</text>'
    )
    svg_h = MARGIN_Y + max(len(starred), 1) * (BAR_H + GAP) + 8

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{svg_h}" viewBox="0 0 {SVG_W} {svg_h}">
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif; fill: #c9d1d9; }}
    .title {{ font-size: 14px; font-weight: 600; fill: #f0f6fc; }}
    .subtitle {{ font-size: 11px; fill: #8b949e; }}
    .label {{ font-size: 11px; }}
    .count {{ font-size: 11px; fill: #8b949e; }}
  </style>
  <rect width="{SVG_W}" height="{svg_h}" rx="8" fill="#0d1117"/>
  <text x="{MARGIN_X}" y="28" class="title">Stars</text>
  <text x="{MARGIN_X}" y="44" class="subtitle">{len(starred)} repos with stars &#183; {total_stars} stars total</text>
{body}
</svg>
"""


if __name__ == "__main__":
    repos = fetch_repos(USERNAME)
    svg = build_chart(repos)
    out = os.path.join(os.path.dirname(__file__), "..", "charts", "star-chart.svg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {out}")
