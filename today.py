"""
Updates the dynamic statistics in light_mode.svg and dark_mode.svg.

Run locally with a .env file (ACCESS_TOKEN=..., USER_NAME=...) or from the
GitHub Actions workflow, which provides both as environment variables.
Without a valid token the script falls back to demo data.
"""

import datetime
import io
import os
import re
import sys
import zipfile

from dateutil import relativedelta
import requests


# ---------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------

BIRTHDAY = "2005-03-07"

GRAPHQL_URL = "https://api.github.com/graphql"
REST_URL = "https://api.github.com"

# Width (in columns) of the info column in the SVG.
LINE_WIDTH = 54

# element id -> key label shown in the SVG (used to size the dot leaders)
DOT_FIELDS = {
    "uptime_data": "Uptime",
    "repo_data": "Repos",
    "star_data": "Stars",
    "follower_data": "Followers",
    "commit_data": "Commits",
    "loc_data": "Lines of Code",
}

SOURCE_EXTENSIONS = (
    ".py", ".js", ".ts", ".html", ".css", ".scss", ".md", ".txt",
    ".json", ".xml", ".yml", ".yaml", ".java", ".c", ".cpp", ".cs",
    ".go", ".rs", ".php", ".rb", ".sh", ".bash", ".zsh", ".fish",
)

EXCLUDED_DIRECTORIES = {
    ".git", "node_modules", "__pycache__", "dist", "build",
    "venv", "env", ".vscode", ".idea",
}

DEMO_STATS = {
    "repos": 8,
    "stars": 45,
    "followers": 12,
    "commits": 287,
    "loc": 12850,
}


# ---------------------------------------------------------------
# Environment
# ---------------------------------------------------------------

def load_env_file():
    env_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ".env",
    )

    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


load_env_file()

TOKEN = os.environ.get("ACCESS_TOKEN", "")
USER_NAME = os.environ.get("USER_NAME", "mucheru-delvan")


def is_token_valid(token):
    if not token or len(token) < 10:
        return False

    if "bluff" in token.lower() or "fake" in token.lower():
        return False

    return True


USE_LIVE_DATA = is_token_valid(TOKEN)

HEADERS = {"authorization": "token " + TOKEN} if USE_LIVE_DATA else {}


# ---------------------------------------------------------------
# GitHub API helpers
#
# These raise on any failure (network error, bad status, GraphQL
# error) so a broken run never writes zeros into the SVGs.
# ---------------------------------------------------------------

def graphql(query, variables):
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    if data.get("errors"):
        raise RuntimeError(f"GitHub GraphQL error: {data['errors']}")

    return data["data"]


def fetch_user():
    """Profile data from the REST API (repo and follower counts)."""
    response = requests.get(
        f"{REST_URL}/users/{USER_NAME}",
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    return response.json()


def fetch_user_id():
    """GraphQL id of the user, used to count only their own commits."""
    data = graphql(
        """
        query($login: String!) {
          user(login: $login) { id }
        }
        """,
        {"login": USER_NAME},
    )

    user = data.get("user")

    if not user:
        raise RuntimeError(f"GitHub user '{USER_NAME}' not found")

    return user["id"]


REPOSITORIES_QUERY = """
query($login: String!, $authorId: ID!, $cursor: String) {
  user(login: $login) {
    repositories(
      first: 100
      after: $cursor
      privacy: PUBLIC
      isFork: false
      ownerAffiliations: OWNER
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        stargazerCount
        owner {
          login
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history(author: { id: $authorId }) {
                totalCount
              }
            }
          }
        }
      }
    }
  }
}
"""


def fetch_repositories(author_id):
    """
    All owned, public, non-fork repositories, with stars and the
    number of commits the user authored on the default branch.
    One paginated query replaces the old per-repository requests.
    """
    repositories = []
    cursor = None

    while True:
        data = graphql(
            REPOSITORIES_QUERY,
            {
                "login": USER_NAME,
                "authorId": author_id,
                "cursor": cursor,
            },
        )

        user = data.get("user")

        if not user:
            raise RuntimeError(f"GitHub user '{USER_NAME}' not found")

        page = user["repositories"]

        repositories.extend(repo for repo in page["nodes"] if repo)

        if not page["pageInfo"]["hasNextPage"]:
            break

        cursor = page["pageInfo"]["endCursor"]

        if not cursor:
            break

    return repositories


def repo_commit_count(repo):
    """Commits by the user on the default branch (0 for empty repos)."""
    branch = repo.get("defaultBranchRef")

    if not branch:
        return 0

    target = branch.get("target") or {}
    history = target.get("history") or {}

    return history.get("totalCount", 0)


def count_repo_loc(owner, name):
    """Lines of code in one repository, from its zip archive."""
    response = requests.get(
        f"{REST_URL}/repos/{owner}/{name}/zipball",
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    loc = 0

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue

            # Skip excluded directories (path parts except the file name).
            directories = member.filename.split("/")[:-1]

            if any(part in EXCLUDED_DIRECTORIES for part in directories):
                continue

            if not member.filename.endswith(SOURCE_EXTENSIONS):
                continue

            with archive.open(member) as file:
                content = file.read().decode("utf-8", errors="ignore")

            loc += len(content.splitlines())

    return loc


# ---------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------

def calculate_uptime(birthday):
    """Time since the start date, e.g. '21 years, 7 months, 0 days'."""
    birth_date = datetime.datetime.strptime(birthday, "%Y-%m-%d").date()

    uptime = relativedelta.relativedelta(
        datetime.date.today(),
        birth_date,
    )

    return (
        f"{uptime.years} years, "
        f"{uptime.months} months, "
        f"{uptime.days} days"
    )


def collect_live_stats():
    print("Fetching live GitHub statistics...")

    user = fetch_user()
    author_id = fetch_user_id()
    repositories = fetch_repositories(author_id)

    print(f"Counting lines of code across {len(repositories)} repositories...")

    total_loc = 0

    for index, repo in enumerate(repositories, start=1):
        owner = repo["owner"]["login"]
        name = repo["name"]

        # Empty repositories have no archive to download.
        if not repo.get("defaultBranchRef"):
            print(f"  [{index}/{len(repositories)}] {owner}/{name} (empty)")
            continue

        repo_loc = count_repo_loc(owner, name)
        total_loc += repo_loc

        print(f"  [{index}/{len(repositories)}] {owner}/{name}: {repo_loc:,} lines")

    return {
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(repo["stargazerCount"] for repo in repositories),
        "commits": sum(repo_commit_count(repo) for repo in repositories),
        "loc": total_loc,
    }


# ---------------------------------------------------------------
# SVG updating
# ---------------------------------------------------------------

def make_dots(key, value):
    """
    Dot leader text so that '. key: <dots> value' is exactly
    LINE_WIDTH columns wide (the value ends at the right edge).

    Layout: '. ' (2) + key + ':' (1) + ' ' + dots + ' ' + value
    """
    count = max(1, LINE_WIDTH - 5 - len(key) - len(value))

    return " " + "." * count + " "


def replace_tspan(content, element_id, new_text):
    pattern = (
        rf'(<tspan[^>]*id="{re.escape(element_id)}"[^>]*>)'
        rf'(.*?)(</tspan>)'
    )

    return re.subn(
        pattern,
        lambda match: match.group(1) + new_text + match.group(3),
        content,
        count=1,
        flags=re.DOTALL,
    )


def update_svg_with_stats_text(svg_content, stats):
    """
    Update the dynamic values and their dot leaders.

    Each value has its own id, and each dot leader has a matching
    '<id>_dots' id, so the right edge stays aligned when a number
    changes length.
    """
    values = {
        "uptime_data": stats["uptime"],
        "repo_data": str(stats["repos"]),
        "star_data": str(stats["stars"]),
        "follower_data": str(stats["followers"]),
        "commit_data": str(stats["commits"]),
        "loc_data": f"{stats['loc']:,}",
    }

    for element_id, value in values.items():
        svg_content, count = replace_tspan(svg_content, element_id, value)

        if count == 0:
            print(f'⚠ Warning: Could not find id="{element_id}" in SVG.')

        dots_id = f"{element_id}_dots"

        svg_content, count = replace_tspan(
            svg_content,
            dots_id,
            make_dots(DOT_FIELDS[element_id], value),
        )

        if count == 0:
            print(f'⚠ Warning: Could not find id="{dots_id}" in SVG.')

    return svg_content


def update_svg_file(path, stats):
    with open(path, "r", encoding="utf-8") as file:
        svg_content = file.read()

    updated_svg = update_svg_with_stats_text(svg_content, stats)

    with open(path, "w", encoding="utf-8") as file:
        file.write(updated_svg)

    print(f"✓ Updated {os.path.basename(path)}")


# ---------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------

def main():
    print("GitHub Profile SVG Updater")
    print("===========================")

    if USE_LIVE_DATA:
        print("🔑 Using live GitHub data from token")

        try:
            stats = collect_live_stats()
        except (requests.RequestException, RuntimeError, KeyError) as error:
            # Fail loudly so the workflow does not commit wrong numbers.
            print(f"✗ Could not fetch GitHub statistics: {error}")
            sys.exit(1)
    else:
        print("⚠️  No valid token found - using demo data")
        stats = dict(DEMO_STATS)

    stats = {**stats, "uptime": calculate_uptime(BIRTHDAY)}

    print(f"Stats to display: {stats}")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    for filename in ("light_mode.svg", "dark_mode.svg"):
        update_svg_file(os.path.join(base_dir, filename), stats)

    print("\n✓ SVG files updated successfully.")


if __name__ == "__main__":
    main()