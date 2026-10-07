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

    <tspan x="500" y="35">delvan@mucheru</tspan>


    <!-- System -->

    <tspan x="500" y="60">. </tspan>
    <tspan class="key">OS</tspan>
    <tspan>: </tspan>
    <tspan class="value">Ubuntu Linux</tspan>

    <tspan x="500" y="78">. </tspan>
    <tspan class="key">Host</tspan>
    <tspan>: </tspan>
    <tspan class="value">HP</tspan>

    <tspan x="500" y="96">. </tspan>
    <tspan class="key">Degree</tspan>
    <tspan>: </tspan>
    <tspan class="value">BSc Microprocessor Technology</tspan>

    <tspan x="500" y="114">. </tspan>
    <tspan class="key">Uptime</tspan>
    <tspan>: </tspan>
    <tspan
        class="value"
        id="uptime_data"
    >21 years, 7 months, 0 days</tspan>

    <tspan x="500" y="132">. </tspan>
    <tspan class="key">Focus</tspan>
    <tspan>: </tspan>
    <tspan class="value">Robust APIs &amp; Scalable Apps</tspan>


    <!-- Programming Languages -->

    <tspan x="500" y="165">- Languages</tspan>

    <tspan x="500" y="183">. </tspan>
    <tspan class="key">Java</tspan>

    <tspan x="500" y="201">. </tspan>
    <tspan class="key">JavaScript</tspan>

    <tspan x="500" y="219">. </tspan>
    <tspan class="key">Python</tspan>

    <tspan x="500" y="237">. </tspan>
    <tspan class="key">SQL</tspan>


    <!-- Contact -->

    <tspan x="500" y="270">- Contact</tspan>

    <tspan x="500" y="288">. </tspan>
    <tspan class="key">Email</tspan>
    <tspan>: </tspan>
    <tspan class="value">mkdelvan9@gmail.com</tspan>

    <tspan x="500" y="306">. </tspan>
    <tspan class="key">LinkedIn</tspan>
    <tspan>: </tspan>
    <tspan class="value">delvan-mucheru</tspan>

    <tspan x="500" y="324">. </tspan>
    <tspan class="key">GitHub</tspan>
    <tspan>: </tspan>
    <tspan class="value">mucheru-delvan</tspan>

    <tspan x="500" y="342">. </tspan>
    <tspan class="key">HackerRank</tspan>
    <tspan>: </tspan>
    <tspan class="value">delvanmucheru</tspan>


    <!-- GitHub Stats -->

    <tspan x="500" y="375">- GitHub Stats</tspan>

    <tspan x="500" y="393">. </tspan>
    <tspan class="key">Repos</tspan>
    <tspan>: </tspan>
    <tspan
        class="value"
        id="repo_data"
    >10</tspan>

    <tspan x="500" y="411">. </tspan>
    <tspan class="key">Stars</tspan>
    <tspan>: </tspan>
    <tspan
        class="value"
        id="star_data"
    >4</tspan>

    <tspan x="500" y="429">. </tspan>
    <tspan class="key">Followers</tspan>
    <tspan>: </tspan>
    <tspan
        class="value"
        id="follower_data"
    >4</tspan>

    <tspan x="500" y="447">. </tspan>
    <tspan class="key">Commits</tspan>
    <tspan>: </tspan>
    <tspan
        class="value"
        id="commit_data"
    >439</tspan>

    <tspan x="500" y="465">. </tspan>
    <tspan class="key">Lines of Code</tspan>
    <tspan>: </tspan>
    <tspan
        class="value"
        id="loc_data"
    >915</tspan>


    <!-- Interests -->

    <tspan x="500" y="498">- Interests</tspan>

    <tspan x="500" y="516">. </tspan>
    <tspan class="key">Primary</tspan>
    <tspan>: </tspan>
    <tspan class="value">Open-source Python Projects</tspan>

    <tspan x="500" y="534">. </tspan>
    <tspan class="key">Open To</tspan>
    <tspan>: </tspan>
    <tspan class="value">Backend Systems</tspan>


    <!-- Fun Fact -->

    <tspan x="500" y="567">- Fun Fact</tspan>

    <tspan x="500" y="585">. </tspan>
    <tspan class="value">Micro-level circuits → Macro-level systems</tspan>

  </text>

</svg>
'''


def main():
    light_path = BASE / "light_mode.svg"
    dark_path = BASE / "dark_mode.svg"

    light_path.write_text(profile_svg(dark=False))
    dark_path.write_text(profile_svg(dark=True))

    print("✓ Rebuilt light_mode.svg")
    print("✓ Rebuilt dark_mode.svg")
    print(f"✓ Imported {len(ASCII)} ASCII-art lines")
    print("✓ Fixed canvas: 985 × 650")
    print("✓ ASCII column: x=15")
    print("✓ ASCII font: 10px")
    print("✓ ASCII line height: 14px")
    print("✓ Terminal column: x=500")
    print("✓ Added languages: Java, JavaScript, Python, SQL")


if __name__ == "__main__":
    main()
