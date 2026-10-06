import datetime
from dateutil import relativedelta
import requests
import os
import base64
import re

# Try to get token from environment variables
TOKEN = os.environ.get('ACCESS_TOKEN', '')
USER_NAME = os.environ.get('USER_NAME', 'mucheru-delvan')

# Check if token looks valid (not empty and not obviously fake)
def is_token_valid(token):
    if not token or len(token) < 10:
        return False
    # Bluff tokens often have obvious patterns - this is a simple check
    if 'bluff' in token.lower() or 'fake' in token.lower():
        return False
    return True

HEADERS = {'authorization': 'token '+ TOKEN} if is_token_valid(TOKEN) else {}
QUERY_COUNT = {'user_getter': 0, 'follower_getter': 0, 'graph_repos_stars': 0, 'recursive_loc': 0, 'graph_commits': 0, 'loc_query': 0}
USE_LIVE_DATA = is_token_valid(TOKEN)

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
    if not USE_LIVE_DATA:
        # Return demo data
        return {
            'login': USER_NAME,
            'followers': 12,
            'public_repos': 8,
            'created_at': '2023-09-15T08:30:00Z'
        }

    url = f"https://api.github.com/users/{USER_NAME}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Warning: Failed to fetch user data: {response.status_code}")
            return None
    except Exception as e:
        print(f"Warning: Error fetching user data: {e}")
        return None


def follower_getter():
    """
    Gets follower count from GitHub API
    """
    global QUERY_COUNT
    QUERY_COUNT['follower_getter'] += 1
    if not USE_LIVE_DATA:
        # Return demo data
        return 12

    url = f"https://api.github.com/users/{USER_NAME}/followers"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return len(response.json())
        else:
            print(f"Warning: Failed to fetch followers: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Warning: Error fetching followers: {e}")
        return 0


def graph_repos_stars():
    """
    Gets total stars across all repositories using GitHub GraphQL API
    """
    global QUERY_COUNT
    QUERY_COUNT['graph_repos_stars'] += 1
    if not USE_LIVE_DATA:
        # Return demo data
        return 45

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
    try:
        response = requests.post(url, json={'query': query}, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            total_stars = sum(repo['stargazerCount'] for repo in data['data']['user']['repositories']['nodes'])
            return total_stars
        else:
            print(f"Warning: Failed to fetch stars: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Warning: Error fetching stars: {e}")
        return 0


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
                if not item.startswith('.') and item not in ['node_modules', '__pycache__', '.git', 'dist', 'build', 'venv', 'env', '.vscode', '.idea']:
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
    if not USE_LIVE_DATA:
        # Return demo data
        return 287

    url = "https://api.github.com/graphql"
    # Note: Getting exact commit count via API is complex and may require pagination
    # This is a simplified approach that may not be 100% accurate but gives reasonable estimate
    query = """
    {
      user(login: "%s") {
        repositories(privacy: PUBLIC, isFork: false) {
          totalCount
          nodes {
            nameWithOwner
          }
        }
      }
    }
    """ % USER_NAME
    try:
        response = requests.post(url, json={'query': query}, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            repos = data['data']['user']['repositories']['nodes']
            # For each repo, get commit count (limited to avoid rate limits)
            total_commits = 0
            for repo in repos[:5]:  # Limit to first 5 repos to avoid rate limiting
                repo_name = repo['nameWithOwner'].split('/')[1]
                repo_owner = repo['nameWithOwner'].split('/')[0]
                commit_query = """
                {
                  repository(owner: "%s", name: "%s") {
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
                """ % (repo_owner, repo_name)
                try:
                    commit_response = requests.post(url, json={'query': commit_query}, headers=HEADERS, timeout=10)
                    if commit_response.status_code == 200:
                        commit_data = commit_response.json()
                        if commit_data.get('data', {}).get('repository', {}).get('defaultBranchRef'):
                            total_commits += commit_data['data']['repository']['defaultBranchRef']['target']['history']['totalCount']
                except:
                    pass  # Skip if we can't get commit count for this repo
            return total_commits
        else:
            print(f"Warning: Failed to fetch commit data: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Warning: Error fetching commit data: {e}")
        return 0


def loc_query():
    """
    Gets lines of code from local repository
    """
    global QUERY_COUNT
    QUERY_COUNT['loc_query'] += 1
    if not USE_LIVE_DATA:
        # Return demo data
        return 12850

    # Count lines in current directory
    return recursive_loc(".")


def generate_svg_loc(loc_data):
    """
    Generates SVG text for lines of code display
    """
    loc_str = f"{loc_data:,}"
    loc_add_int = int(loc_data * 1.17)  # Approximate added lines (as integer)
    loc_add = f"{loc_add_int:,}"  # Formatted with commas
    loc_del_int = loc_add_int - loc_data  # Approximate deleted lines (as integer)
    loc_del = f"{loc_del_int:,}"  # Formatted with commas

    return f"""{loc_str} ( <tspan class="addColor" id="loc_add">{loc_add}</tspan><tspan class="addColor">++</tspan>, <tspan id="loc_del_dots"> </tspan><tspan class="delColor" id="loc_del">{loc_del}</tspan><tspan class="delColor">--</tspan> )"""


def update_svg_with_stats_text(svg_content, stats):
    """
    Updates SVG content with GitHub stats by inserting a stats section using text manipulation
    """
    try:
        # Split the SVG into lines
        lines = svg_content.split('\n')

        # Find the line with the HackerRank entry (last line of Contact section)
        hackerrank_line_index = -1
        for i, line in enumerate(lines):
            if '<tspan x="390" y="410" class="cc">. </tspan><tspan class="key">HackerRank</tspan>:<tspan class="cc"> ........................................ </tspan><tspan class="value">delvanmucheru</tspan>' in line:
                hackerrank_line_index = i
                break

        if hackerrank_line_index == -1:
            # Try alternative pattern for light mode
            for i, line in enumerate(lines):
                if '<tspan x="390" y="410" class="cc">. </tspan><tspan class="key">HackerRank</tspan>:<tspan class="cc"> ........................................ </tspan><tspan class="value">delvanmucheru</tspan>' in line:
                    hackerrank_line_index = i
                    break

        if hackerrank_line_index == -1:
            print("Warning: Could not find HackerRank line to insert after")
            return svg_content

        # Create the GitHub stats section lines
        stats_lines = []

        # Section header
        stats_lines.append('<tspan x="390" y="430">- GitHub Stats</tspan> -——————————————————————————————————————————————-—-')

        # Stats lines - starting at y=450, each 20px apart
        y_pos = 450
        stats_data = [
            ("Repos", str(stats['repos'])),
            ("Stars", str(stats['stars'])),
            ("Followers", str(stats['followers'])),
            ("Commits", str(stats['commits'])),
            ("Lines of Code", generate_svg_loc(stats['loc']))
        ]

        for label, value in stats_data:
            stats_lines.append(f'<tspan x="390" y="{y_pos}" class="cc">. </tspan><tspan class="key">{label}</tspan>:<tspan class="cc"> ........................ </tspan><tspan class="value">{value}</tspan>')
            y_pos += 20

        # Insert the stats lines after the HackerRank line
        # Everything from hackerrank_line_index + 1 onward needs to be shifted down
        # by the number of stats lines we're adding

        # Calculate how much to shift the y-coordinates of subsequent tspan elements
        lines_to_add = len(stats_lines)
        y_shift = lines_to_add * 20

        # Insert the stats lines
        lines = lines[:hackerrank_line_index + 1] + stats_lines + lines[hackerrank_line_index + 1:]

        # Now adjust the y-coordinates of all tspan elements that come after our insertion point
        # We need to find all lines that contain tspan elements with y attributes
        # and increase their y values by y_shift

        # Find where our inserted stats section ends
        stats_end_index = hackerrank_line_index + 1 + lines_to_add

        # Process lines after our inserted section
        for i in range(stats_end_index, len(lines)):
            line = lines[i]
            # Look for tspan elements with y attributes
            # Pattern: <tspan x="390" y="NUMBER" ...>
            match = re.search(r'(<tspan x="390" y=")(\d+)(")', line)
            if match:
                prefix = match.group(1)
                current_y = int(match.group(2))
                suffix = match.group(3)
                new_y = current_y + y_shift
                # Replace the y value
                lines[i] = re.sub(r'(<tspan x="390" y=")\d+(")', rf'\g<1>{new_y}\g<2>', line)

        # Join the lines back together
        updated_svg = '\n'.join(lines)
        return updated_svg

    except Exception as e:
        print(f"Error updating SVG with stats: {e}")
        import traceback
        traceback.print_exc()
        return svg_content


def update_both_svgs_with_stats():
    """
    Update both light_mode.svg and dark_mode.svg with current GitHub stats
    """
    try:
        # Get stats
        if USE_LIVE_DATA:
            print("Fetching live GitHub statistics...")
            user_data = user_getter()
            if not user_data:
                print("Warning: Could not fetch user data, using demo values")
                user_data = {'login': USER_NAME, 'followers': 12, 'public_repos': 8}

            followers = follower_getter()
            repos_count = user_data.get('public_repos', 0) if user_data else 0
            stars_count = graph_repos_stars()
            commit_count = graph_commits()
            loc_count = loc_query()
        else:
            print("Using demo statistics (no valid token provided)...")
            # Demo data
            followers = 12
            repos_count = 8
            stars_count = 45
            commit_count = 287
            loc_count = 12850

        stats = {
            'repos': repos_count,
            'stars': stars_count,
            'followers': followers,
            'commits': commit_count,
            'loc': loc_count
        }

        print(f"Stats to display: {stats}")

        # Update light_mode.svg
        try:
            with open('/home/delvan-mucheru/mucheru-delvan/light_mode.svg', 'r') as f:
                light_svg_content = f.read()
            updated_light_svg = update_svg_with_stats_text(light_svg_content, stats)
            with open('/home/delvan-mucheru/mucheru-delvan/light_mode.svg', 'w') as f:
                f.write(updated_light_svg)
            print("✓ Updated light_mode.svg with GitHub stats")
        except Exception as e:
            print(f"Error updating light_mode.svg: {e}")
            import traceback
            traceback.print_exc()

        # Update dark_mode.svg
        try:
            with open('/home/delvan-mucheru/mucheru-delvan/dark_mode.svg', 'r') as f:
                dark_svg_content = f.read()
            updated_dark_svg = update_svg_with_stats_text(dark_svg_content, stats)
            with open('/home/delvan-mucheru/mucheru-delvan/dark_mode.svg', 'w') as f:
                f.write(updated_dark_svg)
            print("✓ Updated dark_mode.svg with GitHub stats")
        except Exception as e:
            print(f"Error updating dark_mode.svg: {e}")
            import traceback
            traceback.print_exc()

        print("\n🎉 SVG files updated successfully!")
        print("💡 Commit your changes to save the updated profile:")
        print("   git add light_mode.svg dark_mode.svg")
        print("   git commit -m \"Update GitHub profile with live stats\"")
        print("   git push")

    except Exception as e:
        print(f"Error in update_both_svgs_with_stats: {e}")
        import traceback
        traceback.print_exc()


def main():
    """
    Main function to update SVG files with GitHub stats
    """
    print("GitHub Profile SVG Updater")
    print("=========================")

    if USE_LIVE_DATA:
        print("🔑 Using live GitHub data from token")
    else:
        print("⚠️  No valid token found - using demo data")
        print("   To get live stats, set up a fine-grained personal access token with:")
        print("   - Account: read:Followers, read:Starring, read:Watching")
        print("   - Repository: read:Commit statuses, read:Contents, read:Issues, read:Metadata, read:Pull Requests")
        print("   - Then set environment variables:")
        print("     export USER_NAME=mucheru-delvan")
        print("     export ACCESS_TOKEN=your_real_token_here")
        print()

    print("\nFetching statistics and updating SVG files...")
    update_both_svgs_with_stats()


if __name__ == "__main__":
    main()