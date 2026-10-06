import datetime
from dateutil import relativedelta
import requests
import os
from lxml import etree
import time
import hashlib

# Fine-grained personal access token with All Repositories access:
# Account permissions: read:Followers, read:Starring, read:Watching
# Repository permissions: read:Commit statuses, read:Contents, read:Issues, read:Metadata, read:Pull Requests
# Issues and pull request permissions not needed at the moment, but may be used in the future
HEADERS = {'authorization': 'token '+ os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME'] # 'Andrew6rant'
QUERY_COUNT = {'user_getter': 0, 'follower_getter': 0, 'graph_repos_stars': 0, 'recursive_loc': 0, 'graph_commits': 0, 'loc_query': 0}


def daily_readme(birthday):
    """
    Returns the length of time since I was born
    """
    birth_date = datetime.datetime.strptime(birthday, "%Y-%m-%d")
    today = datetime.datetime.today()
    age = relativedelta.relativedelta(today, birth_date)
    return f"{age.years} years, {age.months} months, {age.days} days"


def user_getter():
    """
    Gets user data from GitHub API
    """
    global QUERY_COUNT
    QUERY_COUNT['user_getter'] += 1
    url = f"https://api.github.com/users/{USER_NAME}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch user data: {response.status_code}")


def follower_getter():
    """
    Gets follower count from GitHub API
    """
    global QUERY_COUNT
    QUERY_COUNT['follower_getter'] += 1
    url = f"https://api.github.com/users/{USER_NAME}/followers"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return len(response.json())
    else:
        raise Exception(f"Failed to fetch followers: {response.status_code}")


def graph_repos_stars():
    """
    Gets total stars across all repositories using GitHub GraphQL API
    """
    global QUERY_COUNT
    QUERY_COUNT['graph_repos_stars'] += 1
    url = "https://api.github.com/graphql"
    query = """
    {
      user(login: "%s") {
        repositories(privacy: PUBLIC) {
          totalCount
          nodes {
            stargazerCount
          }
        }
      }
    }
    """ % USER_NAME
    response = requests.post(url, json={'query': query}, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        total_stars = sum(repo['stargazerCount'] for repo in data['data']['user']['repositories']['nodes'])
        return total_stars
    else:
        raise Exception(f"Failed to fetch stars: {response.status_code}")


def recursive_loc(path=".", depth=0, max_depth=10):
    """
    Recursively counts lines of code in a directory
    """
    if depth > max_depth:
        return 0

    loc = 0
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                # Count lines in text files
                if item_path.endswith(('.py', '.js', '.ts', '.html', '.css', '.scss', '.md', '.txt', '.json', '.xml', '.yml', '.yaml', '.java', '.c', '.cpp', '.cs', '.go', '.rs', '.php', '.rb', '.sh', '.bash', '.zsh', '.fish')):
                    try:
                        with open(item_path, 'r', encoding='utf-8', errors='ignore') as f:
                            loc += sum(1 for line in f)
                    except:
                        pass
            elif os.path.isdir(item_path):
                # Skip hidden directories and common ones to avoid
                if not item.startswith('.') and item not in ['node_modules', '__pycache__', '.git', 'dist', 'build', 'venv', 'env']:
                    loc += recursive_loc(item_path, depth+1, max_depth)
    except:
        pass
    return loc


def graph_commits():
    """
    Gets total commit count using GitHub GraphQL API (approximate)
    """
    global QUERY_COUNT
    QUERY_COUNT['graph_commits'] += 1
    url = "https://api.github.com/graphql"
    # Note: This is a simplified approach - getting exact commit count via API is complex
    # This would require pagination through all repositories
    # For demo purposes, we'll use a placeholder or local count
    return 0  # Placeholder - would need actual implementation


def loc_query():
    """
    Gets lines of code from local repository
    """
    global QUERY_COUNT
    QUERY_COUNT['loc_query'] += 1
    # Count lines in current directory
    return recursive_loc(".")


def generate_svg_loc(loc_data):
    """
    Generates SVG text for lines of code display
    """
    loc_str = f"{loc_data:,}"
    loc_add = f"{int(loc_data * 1.17):,}"  # Approximate added lines
    loc_del = f"{int(loc_add - loc_data):,}"  # Approximate deleted lines

    return f"""{loc_str} ( <tspan class="addColor" id="loc_add">{loc_add}</tspan><tspan class="addColor">++</tspan>, <tspan id="loc_del_dots"> </tspan><tspan class="delColor" id="loc_del">{loc_del}</tspan><tspan class="delColor">--</tspan> )"""


def update_readme_with_stats():
    """
    Updates README with generated stats (this would modify the actual README file)
    """
    # This function would be used if you wanted to dynamically generate the README
    # For the SVG approach, we'd generate the SVG files instead
    pass


def main():
    """
    Main function to demonstrate usage
    """
    try:
        # Example usage - in practice, you'd call these functions to get data
        # and then use that data to update your README or SVG files

        print("Today.py script for GitHub profile stats")
        print("=======================================")
        print("This script requires environment variables:")
        print("- ACCESS_TOKEN: GitHub personal access token")
        print("- USER_NAME: Your GitHub username")
        print()
        print("To set environment variables:")
        print("  export ACCESS_TOKEN='your_token_here'")
        print("  export USER_NAME='mucheru-delvan'")
        print()
        print("Or in a .env file:")
        print("  ACCESS_TOKEN=your_token_here")
        print("  USER_NAME=mucheru-delvan")
        print()
        print("Then run: source .env && python today.py")

        # Uncomment the following lines to actually fetch data (requires valid token)
        # user_data = user_getter()
        # print(f"User: {user_data.get('login')}")
        # print(f"Followers: {follower_getter()}")
        # print(f"Total Stars: {graph_repos_stars()}")
        # print(f"Local LOC: {loc_query()}")

    except KeyError as e:
        print(f"Error: Missing environment variable {e}")
        print("Please set ACCESS_TOKEN and USER_NAME environment variables")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()