#!/usr/bin/env python3
"""Refresh the numeric values in the custom profile stats SVG."""
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

USERNAME = os.environ.get("PROFILE_USERNAME", "Vansh-Harit")
SVG = Path("assets/aura-stats.svg")

def get_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-stats-workflow",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

repos = get_json(
    "https://api.github.com/users/" + urllib.parse.quote(USERNAME)
    + "/repos?per_page=100&type=owner&sort=full_name"
)
repo_count = len(repos)
stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos)

# Count commits authored by the profile across its public repositories.
# This is intentionally labeled as a profile snapshot, not a contribution graph clone.
commit_count = 0
for repo in repos:
    page = 1
    while True:
        url = (
            "https://api.github.com/repos/" + USERNAME + "/"
            + urllib.parse.quote(repo["name"])
            + "/commits?author=" + urllib.parse.quote(USERNAME)
            + "&per_page=100&page=" + str(page)
        )
        commits = get_json(url)
        commit_count += len(commits)
        if len(commits) < 100:
            break
        page += 1

text = SVG.read_text(encoding="utf-8")
patterns = {
    "repos": (r'(<text x="143" y="91" class="num" fill="#a78bfa">)\d+(</text>)', repo_count),
    "stars": (r'(<text x="430" y="91" class="num" fill="#60a5fa">)\d+(</text>)', stars),
    "commits": (r'(<text x="716" y="91" class="num" fill="#fbbf24">)\d+(</text>)', commit_count),
}
for name, (pattern, value) in patterns.items():
    text, replacements = re.subn(pattern, rf'\g<1>{value}\g<2>', text, count=1)
    if replacements != 1:
        raise RuntimeError(f"Could not update {name} in {SVG}")
SVG.write_text(text, encoding="utf-8")
print(f"Updated stats: repos={repo_count}, stars={stars}, commits={commit_count}")
