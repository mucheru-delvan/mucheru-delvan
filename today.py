import datetime
from dateutil import relativedelta
import requests
import os


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


HEADERS = (
    {"authorization": "token " + TOKEN}
    if is_token_valid(TOKEN)
    else {}
)

USE_LIVE_DATA = is_token_valid(TOKEN)


def calculate_uptime(birthday):
    """
    Returns the length of time since I was born.
    """
    birth_date = datetime.datetime.strptime(
        birthday,
        "%Y-%m-%d",
    )

    today = datetime.datetime.today()

    uptime = relativedelta.relativedelta(
        today,
        birth_date,
    )

    return (
        f"{uptime.years} years, "
        f"{uptime.months} months, "
        f"{uptime.days} days"
    )


def user_getter():
    """
    Gets user data from GitHub API.
    """
    if not USE_LIVE_DATA:
        return {
            "login": USER_NAME,
            "followers": 12,
            "public_repos": 8,
            "created_at": "2023-09-15T08:30:00Z",
        }

    url = f"https://api.github.com/users/{USER_NAME}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()

        print(
            "Warning: Failed to fetch user data: "
            f"{response.status_code}"
        )

        return None

    except Exception as e:
        print(
            "Warning: Error fetching user data: "
            f"{e}"
        )

        return None


def follower_getter():
    """
    Gets follower count from GitHub API.
    """
    if not USE_LIVE_DATA:
        return 12

    url = f"https://api.github.com/users/{USER_NAME}/followers"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
        )

        if response.status_code == 200:
            return len(response.json())

        print(
            "Warning: Failed to fetch followers: "
            f"{response.status_code}"
        )

        return 0

    except Exception as e:
        print(
            "Warning: Error fetching followers: "
            f"{e}"
        )

        return 0


def graph_repos_stars():
    """
    Gets total stars across all public repositories
    using GitHub GraphQL API.
    """
    if not USE_LIVE_DATA:
        return 45

    url = "https://api.github.com/graphql"

    query = """
    query($login: String!, $cursor: String) {
      user(login: $login) {
        repositories(
          first: 100
          after: $cursor
          privacy: PUBLIC
          ownerAffiliations: OWNER
        ) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            stargazerCount
          }
        }
      }
    }
    """

    try:
        total_stars = 0
        cursor = None

        while True:
            response = requests.post(
                url,
                json={
                    "query": query,
                    "variables": {
                        "login": USER_NAME,
                        "cursor": cursor,
                    },
                },
                headers=HEADERS,
                timeout=15,
            )

            if response.status_code != 200:
                print(
                    "Warning: Failed to fetch stars: "
                    f"{response.status_code}"
                )

                return 0

            data = response.json()

            if data.get("errors"):
                print(
                    "Warning: GitHub GraphQL error "
                    "fetching stars: "
                    f"{data['errors']}"
                )

                return 0

            user = data.get("data", {}).get("user")

            if not user:
                print(
                    "Warning: GitHub user data missing "
                    "while fetching stars"
                )

                return 0

            repositories = user.get("repositories")

            if not repositories:
                return 0

            for repo in repositories.get("nodes", []):
                if repo:
                    total_stars += repo.get(
                        "stargazerCount",
                        0,
                    )

            page_info = repositories.get(
                "pageInfo",
                {},
            )

            if not page_info.get("hasNextPage"):
                break

            cursor = page_info.get("endCursor")

            if not cursor:
                break

        return total_stars

    except Exception as e:
        print(
            "Warning: Error fetching stars: "
            f"{e}"
        )

        return 0


def recursive_loc(path=".", depth=0, max_depth=10):
    """
    Recursively counts lines of code in the local repository.
    """
    if depth > max_depth:
        return 0

    loc = 0

    try:
        for item in os.listdir(path):
            item_path = os.path.join(
                path,
                item,
            )

            if os.path.isfile(item_path):
                if item_path.endswith(
                    (
                        ".py",
                        ".js",
                        ".ts",
                        ".html",
                        ".css",
                        ".scss",
                        ".md",
                        ".txt",
                        ".json",
                        ".xml",
                        ".yml",
                        ".yaml",
                        ".java",
                        ".c",
                        ".cpp",
                        ".cs",
                        ".go",
                        ".rs",
                        ".php",
                        ".rb",
                        ".sh",
                        ".bash",
                        ".zsh",
                        ".fish",
                    )
                ):
                    try:
                        with open(
                            item_path,
                            "r",
                            encoding="utf-8",
                            errors="ignore",
                        ) as f:
                            loc += sum(
                                1
                                for line in f
                            )

                    except Exception:
                        pass

            elif os.path.isdir(item_path):
                if (
                    not item.startswith(".")
                    and item
                    not in [
                        "node_modules",
                        "__pycache__",
                        ".git",
                        "dist",
                        "build",
                        "venv",
                        "env",
                        ".vscode",
                        ".idea",
                    ]
                ):
                    loc += recursive_loc(
                        item_path,
                        depth + 1,
                        max_depth,
                    )

    except Exception:
        pass

    return loc


def graph_commits():
    """
    Gets commit count across all owned public repositories.
    """
    if not USE_LIVE_DATA:
        return 287

    url = "https://api.github.com/graphql"

    repo_query = """
    query($login: String!, $cursor: String) {
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
            nameWithOwner
            owner {
              login
            }
          }
        }
      }
    }
    """

    commit_query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        defaultBranchRef {
          target {
            ... on Commit {
              history {
                totalCount
              }
            }
          }
        }
      }
    }
    """

    try:
        repositories = []
        cursor = None

        while True:
            response = requests.post(
                url,
                json={
                    "query": repo_query,
                    "variables": {
                        "login": USER_NAME,
                        "cursor": cursor,
                    },
                },
                headers=HEADERS,
                timeout=15,
            )

            if response.status_code != 200:
                print(
                    "Warning: Failed to fetch "
                    "repository data: "
                    f"{response.status_code}"
                )

                return 0

            data = response.json()

            if data.get("errors"):
                print(
                    "Warning: GitHub GraphQL error "
                    "fetching repositories: "
                    f"{data['errors']}"
                )

                return 0

            user = data.get(
                "data",
                {},
            ).get("user")

            if not user:
                print(
                    "Warning: GitHub user data missing "
                    "while fetching commits"
                )

                return 0

            repo_data = user.get("repositories")

            if not repo_data:
                return 0

            repositories.extend(
                repo
                for repo in repo_data.get("nodes", [])
                if repo
            )

            page_info = repo_data.get(
                "pageInfo",
                {},
            )

            if not page_info.get("hasNextPage"):
                break

            cursor = page_info.get("endCursor")

            if not cursor:
                break

        total_commits = 0

        for repo in repositories:
            owner = repo.get(
                "owner",
                {},
            ).get("login")

            name = repo.get("name")

            if not owner or not name:
                continue

            try:
                commit_response = requests.post(
                    url,
                    json={
                        "query": commit_query,
                        "variables": {
                            "owner": owner,
                            "name": name,
                        },
                    },
                    headers=HEADERS,
                    timeout=10,
                )

                if commit_response.status_code != 200:
                    continue

                commit_data = commit_response.json()

                if commit_data.get("errors"):
                    continue

                repository = (
                    commit_data
                    .get("data", {})
                    .get("repository")
                )

                if not repository:
                    continue

                default_branch = repository.get(
                    "defaultBranchRef"
                )

                if not default_branch:
                    continue

                target = default_branch.get("target")

                if not target:
                    continue

                history = target.get("history")

                if not history:
                    continue

                total_commits += history.get(
                    "totalCount",
                    0,
                )

            except Exception:
                continue

        return total_commits

    except Exception as e:
        print(
            "Warning: Error fetching commit data: "
            f"{e}"
        )

        return 0


def loc_query():
    """
    Gets lines of code from the local repository.
    """
    if not USE_LIVE_DATA:
        return 12850

    return recursive_loc(".")


def generate_svg_loc(loc_data):
    """
    Generates SVG text for the Lines of Code statistic.
    """
    loc_str = f"{loc_data:,}"

    loc_add_int = int(loc_data * 1.17)
    loc_add = f"{loc_add_int:,}"

    loc_del_int = loc_add_int - loc_data
    loc_del = f"{loc_del_int:,}"

    return (
        f'{loc_str} ( '
        f'<tspan class="addColor" id="loc_add">'
        f'{loc_add}</tspan>'
        f'<tspan class="addColor">++</tspan>, '
        f'<tspan id="loc_del_dots"> </tspan>'
        f'<tspan class="delColor" id="loc_del">'
        f'{loc_del}</tspan>'
        f'<tspan class="delColor">--</tspan> )'
    )


def update_svg_with_stats_text(svg_content, stats):
    """
    Replace the existing GitHub Stats values.
    """

    lines = svg_content.splitlines()

    # ---------------------------------------------------------
    # Update Year -> Uptime
    # ---------------------------------------------------------

    uptime = stats["uptime"]

    for index, line in enumerate(lines):
        if (
            'id="tspan138"' in line
            and ">Year</tspan>" in line
        ):
            lines[index] = line.replace(
                ">Year</tspan>",
                ">Uptime</tspan>",
            )

        if "Fourth Year" in line:
            lines[index] = line.replace(
                "Fourth Year",
                uptime,
            )

    # ---------------------------------------------------------
    # Existing GitHub statistics
    # ---------------------------------------------------------

    replacements = {
        "Repos": str(stats["repos"]),
        "Stars": str(stats["stars"]),
        "Followers": str(stats["followers"]),
        "Commits": str(stats["commits"]),
        "Lines of Code": generate_svg_loc(
            stats["loc"]
        ),
    }

    # Find each statistic label and replace the
    # corresponding value in the following SVG lines.
    for index, line in enumerate(lines):

        for label, value in replacements.items():

            if f">{label}</tspan>" not in line:
                continue

            for next_index in range(
                index + 1,
                min(index + 8, len(lines)),
            ):
                if 'class="value"' in lines[next_index]:

                    value_line = lines[next_index]

                    start = value_line.find(">")

                    end = value_line.rfind("<")

                    if start != -1 and end != -1:
                        lines[next_index] = (
                            value_line[: start + 1]
                            + value
                            + value_line[end:]
                        )

                    break

    return "\n".join(lines)


def update_svg_file(path, stats):
    """
    Update one SVG file without changing its layout.
    """
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        svg_content = file.read()

    updated_svg = update_svg_with_stats_text(
        svg_content,
        stats,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(updated_svg)

    print(
        f"✓ Updated {os.path.basename(path)}"
    )


def update_both_svgs_with_stats():
    """
    Fetch statistics and update both SVG files.
    """

    if USE_LIVE_DATA:
        print(
            "Fetching live GitHub statistics..."
        )

        user_data = user_getter()

        if not user_data:
            print(
                "Warning: Could not fetch user data."
            )

            return

        repos_count = user_data.get(
            "public_repos",
            0,
        )

        followers = follower_getter()
        stars_count = graph_repos_stars()
        commit_count = graph_commits()
        loc_count = loc_query()

    else:
        print(
            "Using demo statistics "
            "(no valid token provided)..."
        )

        repos_count = 8
        stars_count = 45
        followers = 12
        commit_count = 287
        loc_count = 12850

    # ---------------------------------------------------------
    # All statistics displayed in the SVG
    # ---------------------------------------------------------

    stats = {
        "repos": repos_count,
        "stars": stars_count,
        "followers": followers,
        "commits": commit_count,
        "loc": loc_count,
        "uptime": calculate_uptime(
            "2005-03-07"
        ),
    }

    print(
        f"Stats to display: {stats}"
    )

    base_dir = (
        "/home/delvan-mucheru/"
        "mucheru-delvan"
    )

    light_path = os.path.join(
        base_dir,
        "light_mode.svg",
    )

    dark_path = os.path.join(
        base_dir,
        "dark_mode.svg",
    )

    update_svg_file(
        light_path,
        stats,
    )

    update_svg_file(
        dark_path,
        stats,
    )

    print(
        "\n✓ SVG files updated successfully."
    )

    print(
        "✓ Existing GitHub Stats section "
        "was updated in place."
    )

    print(
        "✓ Year field replaced with Uptime."
    )


def main():
    print(
        "GitHub Profile SVG Updater"
    )

    print(
        "==========================="
    )

    if USE_LIVE_DATA:
        print(
            "🔑 Using live GitHub data from token"
        )
    else:
        print(
            "⚠️  No valid token found - "
            "using demo data"
        )

    print(
        "\nFetching statistics and "
        "updating SVG files..."
    )

    update_both_svgs_with_stats()


if __name__ == "__main__":
    main()