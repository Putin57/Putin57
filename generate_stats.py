import requests
import os
import json
from datetime import datetime

USERNAME = os.environ.get("USERNAME", "Putin57")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

headers = {
    "Authorization": f"bearer {TOKEN}",
    "Content-Type": "application/json"
}

query = """
query($username: String!) {
  user(login: $username) {
    name
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER) {
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
    pullRequests(states: [OPEN, MERGED, CLOSED]) {
      totalCount
    }
    issues(states: [OPEN, CLOSED]) {
      totalCount
    }
  }
}
"""

response = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"username": USERNAME}},
    headers=headers
)

data = response.json()["data"]["user"]

total_stars = sum(r["stargazerCount"] for r in data["repositories"]["nodes"])
total_commits = data["contributionsCollection"]["totalCommitContributions"]
total_prs = data["pullRequests"]["totalCount"]
total_issues = data["issues"]["totalCount"]

all_days = []
for week in data["contributionsCollection"]["contributionCalendar"]["weeks"]:
    for day in week["contributionDays"]:
        all_days.append(day)

all_days.sort(key=lambda x: x["date"], reverse=True)

current_streak = 0
longest_streak = 0
temp_streak = 0

for day in all_days:
    if day["contributionCount"] > 0:
        temp_streak += 1
        longest_streak = max(longest_streak, temp_streak)
    else:
        if current_streak == 0 and temp_streak > 0:
            current_streak = temp_streak
        temp_streak = 0

if current_streak == 0:
    current_streak = temp_streak

lang_sizes = {}
for repo in data["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        name = edge["node"]["name"]
        size = edge["size"]
        lang_sizes[name] = lang_sizes.get(name, 0) + size

total_size = sum(lang_sizes.values())
lang_percentages = {k: (v/total_size)*100 for k, v in sorted(lang_sizes.items(), key=lambda x: -x[1])[:6]}

os.makedirs("assets", exist_ok=True)

stats = {
    "stars": total_stars,
    "commits": total_commits,
    "prs": total_prs,
    "issues": total_issues,
    "current_streak": current_streak,
    "longest_streak": longest_streak,
    "languages": lang_percentages,
    "updated": datetime.now().strftime("%Y-%m-%d %H:%M UTC")
}

with open("assets/stats.json", "w") as f:
    json.dump(stats, f)


def generate_stats_svg(stats):
    commits_display = f"{stats['commits']//1000}k" if stats['commits'] >= 1000 else str(stats['commits'])
    stars = stats['stars']
    prs = stats['prs']
    issues = stats['issues']
    commits_val = stats['commits']
    return f'''<svg width="495" height="195" xmlns="http://www.w3.org/2000/svg">
  <style>
    .title {{ font: bold 16px "Segoe UI", sans-serif; fill: #7FFF00; }}
    .stat-label {{ font: 14px "Segoe UI", sans-serif; fill: #a0a0a0; }}
    .stat-value {{ font: bold 15px "Segoe UI", sans-serif; fill: #ffffff; }}
  </style>
  <rect width="495" height="195" rx="10" fill="#0d1117"/>
  <rect x="1" y="1" width="493" height="193" rx="9" fill="none" stroke="#7FFF00" stroke-width="0.5" opacity="0.3"/>

  <text x="25" y="35" class="title">Putin57s GitHub Stats</text>

  <text x="25" y="72" class="stat-label">⭐ Total Stars Earned:</text>
  <text x="230" y="72" class="stat-value">{stars}</text>

  <text x="25" y="97" class="stat-label">🕐 Total Commits:</text>
  <text x="230" y="97" class="stat-value">{commits_display}</text>

  <text x="25" y="122" class="stat-label">🔀 Total PRs:</text>
  <text x="230" y="122" class="stat-value">{prs}</text>

  <text x="25" y="147" class="stat-label">⚠ Total Issues:</text>
  <text x="230" y="147" class="stat-value">{issues}</text>

  <circle cx="400" cy="100" r="55" fill="none" stroke="#333" stroke-width="8"/>
  <circle cx="400" cy="100" r="55" fill="none" stroke="#7FFF00" stroke-width="8"
    stroke-dasharray="345" stroke-dashoffset="86" stroke-linecap="round"
    transform="rotate(-90 400 100)"/>
  <text x="400" y="93" text-anchor="middle" font-size="13" fill="#aaa">Total</text>
  <text x="400" y="115" text-anchor="middle" font-size="18" font-weight="bold" fill="white">{commits_val}</text>
</svg>'''


def generate_streak_svg(stats):
    current = stats['current_streak']
    longest = stats['longest_streak']
    updated = stats['updated']
    return f'''<svg width="495" height="195" xmlns="http://www.w3.org/2000/svg">
  <style>
    .label {{ font: 13px "Segoe UI", sans-serif; fill: #a0a0a0; }}
    .value {{ font: bold 26px "Segoe UI", sans-serif; fill: #ffffff; }}
    .small {{ font: 12px "Segoe UI", sans-serif; fill: #7FFF00; }}
  </style>
  <rect width="495" height="195" rx="10" fill="#0d1117"/>
  <rect x="1" y="1" width="493" height="193" rx="9" fill="none" stroke="#7FFF00" stroke-width="0.5" opacity="0.3"/>

  <text x="90" y="95" text-anchor="middle" class="value">{current}</text>
  <text x="90" y="118" text-anchor="middle" class="small">Current Streak</text>
  <text x="90" y="140" text-anchor="middle" font-size="16" fill="#aaa">🔥</text>

  <circle cx="247" cy="97" r="45" fill="none" stroke="#333" stroke-width="6"/>
  <circle cx="247" cy="97" r="45" fill="none" stroke="#7FFF00" stroke-width="6"
    stroke-dasharray="283" stroke-dashoffset="70"
    stroke-linecap="round" transform="rotate(-90 247 97)"/>
  <text x="247" y="105" text-anchor="middle" font-size="26" fill="white">🔥</text>

  <text x="400" y="95" text-anchor="middle" class="value">{longest}</text>
  <text x="400" y="118" text-anchor="middle" class="small">Longest Streak</text>

  <text x="247" y="172" text-anchor="middle" font-size="11" fill="#555">Updated: {updated}</text>
</svg>'''


def generate_langs_svg(stats):
    langs = stats['languages']
    colors = {
        'Python': '#3572A5', 'JavaScript': '#f1e05a', 'TypeScript': '#2b7489',
        'Java': '#b07219', 'C++': '#f34b7d', 'C': '#555555',
        'Jupyter Notebook': '#DA5B0B', 'Cython': '#fedf5b', 'HTML': '#e34c26',
        'CSS': '#563d7c', 'Go': '#00ADD8', 'Rust': '#dea584',
        'Assembly': '#6E4C13'
    }

    bar_x = 25
    bar_width = 445
    bar_parts = ""
    x = bar_x
    for lang, pct in langs.items():
        w = int((pct / 100) * bar_width)
        color = colors.get(lang, '#888888')
        bar_parts += f'<rect x="{x}" y="55" width="{w}" height="12" fill="{color}" rx="3"/>'
        x += w

    legend = ""
    items = list(langs.items())
    for i, (lang, pct) in enumerate(items):
        col = i % 2
        row = i // 2
        lx = 45 + col * 230
        ly = 90 + row * 28
        color = colors.get(lang, '#888888')
        pct_str = f"{pct:.2f}%"
        legend += f'<circle cx="{lx-15}" cy="{ly-5}" r="6" fill="{color}"/>'
        legend += f'<text x="{lx}" y="{ly}" font-size="13" fill="#ccc" font-family="Segoe UI">{lang} {pct_str}</text>'

    height = 90 + (len(items)//2 + 1) * 28 + 20
    return f'''<svg width="495" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="495" height="{height}" rx="10" fill="#0d1117"/>
  <rect x="1" y="1" width="493" height="{height-2}" rx="9" fill="none" stroke="#7FFF00" stroke-width="0.5" opacity="0.3"/>
  <text x="25" y="35" font-size="16" font-weight="bold" fill="#7FFF00" font-family="Segoe UI">Most Used Languages</text>
  {bar_parts}
  {legend}
</svg>'''


with open("assets/stats.svg", "w") as f:
    f.write(generate_stats_svg(stats))

with open("assets/streak.svg", "w") as f:
    f.write(generate_streak_svg(stats))

with open("assets/langs.svg", "w") as f:
    f.write(generate_langs_svg(stats))

print("Stats generated successfully!")
print(json.dumps(stats, indent=2))
