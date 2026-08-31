"""
Generate a repo stats bar chart SVG from GitHub API.
Shows top repos by stars + forks.
Output: charts/repo-stats.svg
"""
import json, urllib.request, os

USERNAME = "dboycht"
TOP_N = 10
BAR_MAX_W = 280
BAR_H = 16
GAP = 6
MARGIN_X, MARGIN_Y = 20, 40

def fetch_repos(username):
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=stars&direction=desc"
    req = urllib.request.Request(url, headers={"User-Agent": "dboycht-readme"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def build_chart(repos):
    # Filter out forks, take top N by stars+forks
    filtered = [r for r in repos if not r["fork"]]
    filtered.sort(key=lambda r: r["stargazers_count"] + r["forks_count"], reverse=True)
    top = filtered[:TOP_N]

    max_val = max((r["stargazers_count"] + r["forks_count"] for r in top), default=1) or 1
    rows = []
    for i, r in enumerate(top):
        y = MARGIN_Y + i * (BAR_H + GAP)
        stars = r["stargazers_count"]
        forks = r["forks_count"]
        total = stars + forks
        w = max(int(total / max_val * BAR_MAX_W), 4)
        name = r["name"][:20]
        lang_color = get_lang_color(r.get("language"))
        rows.append(
            f'<text x="{MARGIN_X}" y="{y + 12}" font-size="11" fill="#c9d1d9">{name}</text>'
            f'<rect x="170" y="{y}" width="{w}" height="{BAR_H}" rx="3" fill="{lang_color}"/>'
            f'<text x="{170 + w + 6}" y="{y + 12}" font-size="10" fill="#8b949e">⭐{stars} 🍴{forks}</text>'
        )

    svg_h = MARGIN_Y + TOP_N * (BAR_H + GAP) + 10
    svg_w = 480
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">
  <style>text {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif; }}</style>
  <rect width="{svg_w}" height="{svg_h}" rx="8" fill="#0d1117"/>
  <text x="{MARGIN_X}" y="24" font-size="13" font-weight="600" fill="#f0f6fc">Top Repositories by Stars + Forks</text>
  {''.join(rows)}
</svg>"""


LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Rust": "#dea584", "C#": "#178600", "HTML": "#e34c26", "CSS": "#563d7c",
    "PowerShell": "#012456", "Jupyter Notebook": "#DA5B0B",
}

def get_lang_color(lang):
    return LANG_COLORS.get(lang, "#8b949e")


if __name__ == "__main__":
    repos = fetch_repos(USERNAME)
    svg = build_chart(repos)
    out = os.path.join(os.path.dirname(__file__), "..", "charts", "repo-stats.svg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {out}")
