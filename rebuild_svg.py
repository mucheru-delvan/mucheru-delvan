from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "svg-backup" / "light_mode.svg"


def extract_ascii():
    """Extract the existing ASCII artwork from the original SVG."""

    svg = SOURCE.read_text()

    match = re.search(
        r'<text[^>]*id="text134"[^>]*>(.*?)</text>',
        svg,
        re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            'Could not find the existing ASCII block with id="text134".'
        )

    block = match.group(1)

    lines = re.findall(
        r'<tspan[^>]*>(.*?)</tspan>',
        block,
        re.DOTALL,
    )

    if not lines:
        raise RuntimeError(
            "ASCII block was found, but no lines were extracted."
        )

    cleaned = []

    for line in lines:
        line = line.replace("&amp;", "&")
        line = line.replace("&lt;", "<")
        line = line.replace("&gt;", ">")
        cleaned.append(line)

    return cleaned


ASCII = extract_ascii()


def esc(text):
    """Escape text for XML."""

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def ascii_block():
    """
    Render the ASCII artwork as an independent
    left-hand text block.
    """

    x = 15
    y = 50
    line_height = 14

    output = []

    for index, line in enumerate(ASCII):
        output.append(
            f'    <tspan x="{x}" y="{y + index * line_height}">'
            f'{esc(line)}'
            f'</tspan>'
        )

    return "\n".join(output)


def profile_line(x, y, content):
    """
    Create a complete terminal line with explicit x/y positioning.

    The outer tspan controls the position.
    Nested tspans are used only for styling.
    """

    return f'''    <tspan x="{x}" y="{y}">
{content}
    </tspan>'''


def styled_line(x, y, prefix, key, value):
    """
    Create a profile line with explicit positioning
    and separate colors for the key and value.
    """

    return f'''    <tspan x="{x}" y="{y}"><tspan class="cc">{esc(prefix)}</tspan><tspan class="key">{esc(key)}</tspan><tspan class="cc">: </tspan><tspan class="value">{esc(value)}</tspan></tspan>'''


def bullet_line(x, y, text, style="key"):
    """
    Create a bullet-style profile line.

    The complete line gets explicit x/y positioning.
    """

    return f'''    <tspan x="{x}" y="{y}"><tspan class="cc">. </tspan><tspan class="{style}">{esc(text)}</tspan></tspan>'''


def profile_svg(dark=True):
    """Build a clean fixed-size profile SVG."""

    if dark:
        bg = "#161b22"
        fg = "#c9d1d9"
        cc = "#8b949e"
        key = "#79c0ff"
        value = "#a5d6ff"
    else:
        bg = "#f6f8fa"
        fg = "#24292f"
        cc = "#57606a"
        key = "#0550ae"
        value = "#0969da"

    ascii_lines = ascii_block()

    return f'''<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="985px"
    height="650px"
    font-family="ConsolasFallback, Consolas, monospace"
    font-size="16px"
>

  <style>

    @font-face {{
      font-family: ConsolasFallback;
      src: local("DejaVu Sans Mono");
    }}

    text,
    tspan {{
      white-space: pre;
    }}

    .ascii {{
      font-family: ConsolasFallback, Consolas, monospace;
      font-size: 10px;
      fill: {fg};
    }}

    .terminal {{
      font-family: ConsolasFallback, Consolas, monospace;
      font-size: 14px;
      fill: {fg};
    }}

    .key {{
      fill: {key};
    }}

    .value {{
      fill: {value};
    }}

    .cc {{
      fill: {cc};
    }}

  </style>


  <!-- ========================================================= -->
  <!-- BACKGROUND                                                -->
  <!-- ========================================================= -->

  <rect
      x="0"
      y="0"
      width="985"
      height="650"
      rx="15"
      fill="{bg}"
  />


  <!-- ========================================================= -->
  <!-- LEFT COLUMN — ASCII ART                                  -->
  <!-- ========================================================= -->

  <text
      class="ascii"
      x="15"
      y="50"
  >
{ascii_lines}
  </text>


  <!-- ========================================================= -->
  <!-- RIGHT COLUMN — PROFILE INFORMATION                        -->
  <!-- ========================================================= -->

  <text
      class="terminal"
      x="500"
      y="35"
  >

    <!-- Header -->

    <tspan x="500" y="35"><tspan class="cc">delvan@mucheru</tspan></tspan>


    <!-- System -->

{styled_line(500, 60, ". ", "OS", "Ubuntu Linux")}
{styled_line(500, 78, ". ", "Host", "HP")}
{styled_line(500, 96, ". ", "Degree", "BSc Microprocessor Technology")}

    <tspan x="500" y="114"><tspan class="cc">. </tspan><tspan class="key">Uptime</tspan><tspan class="cc">: </tspan><tspan class="value" id="uptime_data">21 years, 7 months, 0 days</tspan></tspan>

{styled_line(500, 132, ". ", "Focus", "Robust APIs & Scalable Apps")}


    <!-- Programming Languages -->

    <tspan x="500" y="165"><tspan class="cc">- </tspan><tspan class="key">Languages</tspan></tspan>

{bullet_line(500, 183, "Java")}
{bullet_line(500, 201, "JavaScript")}
{bullet_line(500, 219, "Python")}
{bullet_line(500, 237, "SQL")}


    <!-- Contact -->

    <tspan x="500" y="270"><tspan class="cc">- </tspan><tspan class="key">Contact</tspan></tspan>

{styled_line(500, 288, ". ", "Email", "mkdelvan9@gmail.com")}
{styled_line(500, 306, ". ", "LinkedIn", "delvan-mucheru")}
{styled_line(500, 324, ". ", "GitHub", "mucheru-delvan")}
{styled_line(500, 342, ". ", "HackerRank", "delvanmucheru")}


    <!-- GitHub Stats -->

    <tspan x="500" y="375"><tspan class="cc">- </tspan><tspan class="key">GitHub Stats</tspan></tspan>

    <tspan x="500" y="393"><tspan class="cc">. </tspan><tspan class="key">Repos</tspan><tspan class="cc">: </tspan><tspan class="value" id="repo_data">10</tspan></tspan>

    <tspan x="500" y="411"><tspan class="cc">. </tspan><tspan class="key">Stars</tspan><tspan class="cc">: </tspan><tspan class="value" id="star_data">4</tspan></tspan>

    <tspan x="500" y="429"><tspan class="cc">. </tspan><tspan class="key">Followers</tspan><tspan class="cc">: </tspan><tspan class="value" id="follower_data">4</tspan></tspan>

    <tspan x="500" y="447"><tspan class="cc">. </tspan><tspan class="key">Commits</tspan><tspan class="cc">: </tspan><tspan class="value" id="commit_data">439</tspan></tspan>

    <tspan x="500" y="465"><tspan class="cc">. </tspan><tspan class="key">Lines of Code</tspan><tspan class="cc">: </tspan><tspan class="value" id="loc_data">915</tspan></tspan>


    <!-- Interests -->

    <tspan x="500" y="498"><tspan class="cc">- </tspan><tspan class="key">Interests</tspan></tspan>

{styled_line(500, 516, ". ", "Primary", "Open-source Python Projects")}
{styled_line(500, 534, ". ", "Open To", "Backend Systems")}


    <!-- Fun Fact -->

    <tspan x="500" y="567"><tspan class="cc">- </tspan><tspan class="key">Fun Fact</tspan></tspan>

    <tspan x="500" y="585"><tspan class="cc">. </tspan><tspan class="value">Micro-level circuits → Macro-level systems</tspan></tspan>

  </text>

</svg>
'''


def main():
    light_path = BASE / "light_mode.svg"
    dark_path = BASE / "dark_mode.svg"

    light_path.write_text(
        profile_svg(dark=False),
        encoding="utf-8",
    )

    dark_path.write_text(
        profile_svg(dark=True),
        encoding="utf-8",
    )

    print("✓ Rebuilt light_mode.svg")
    print("✓ Rebuilt dark_mode.svg")
    print(f"✓ Imported {len(ASCII)} ASCII-art lines")
    print("✓ Fixed canvas: 985 × 650")
    print("✓ ASCII column: x=15")
    print("✓ ASCII font: 10px")
    print("✓ ASCII line height: 14px")
    print("✓ Terminal column: x=500")
    print("✓ Terminal font: 14px")
    print("✓ Added languages: Java, JavaScript, Python, SQL")


if __name__ == "__main__":
    main()