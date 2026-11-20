# README image 5: the other alternates, default on the left, alternate on the
# right.
#
# Run from the root of the repository after building the fonts:
#   python3 documentation/image5.py --output documentation/image5.png
# `make images` runs every documentation/image*.py this way.
import argparse

from drawbot_skia.drawbot import *

FONT = "fonts/variable/PentasMeongSeru[wght].ttf"
CREAM = (250 / 255, 246 / 255, 224 / 255)
RED = (170 / 255, 48 / 255, 44 / 255)
INK = (25 / 255, 25 / 255, 25 / 255)
GREY = (120 / 255, 120 / 255, 120 / 255)
ROWS = [
    ("ss01", "abdglopqtu"),
    ("ss02", "ai"),
    ("ss03", "gIW"),
    ("ss04", "0"),
    ("cv19", "k"),
    ("cv20", "4"),
    ("ss09", "?"),
]
MARGIN, DEFAULT_X, ARROW_X, ALTERNATE_X = 80, 240, 820, 920
SIZE, WGHT, FIRST_BASELINE, LINE_HEIGHT = 96, 700, 150, 124
WIDTH, HEIGHT = 1600, FIRST_BASELINE + (len(ROWS) - 1) * LINE_HEIGHT + 70


def ink_top(txt, size):
    """The height of `txt`'s ink above the baseline at `size` px."""
    path = BezierPath()
    path.text(txt, font=FONT, fontSize=size)
    return path.bounds()[3]


def centred(txt, x, centre, size, wght, color):
    """Draws `txt` with its ink centred vertically on `centre`."""
    path = BezierPath()
    path.text(txt, font=FONT, fontSize=size)
    bottom, top = path.bounds()[1], path.bounds()[3]
    glyphs(txt, x, centre - (bottom + top) / 2, size, wght, color)


def glyphs(txt, x, y, size, wght, color, *features):
    fill(*color)
    font(FONT, size)
    fontVariations(wght=wght)
    openTypeFeatures(resetFeatures=True, **{tag: True for tag in features})
    text(txt, (x, y))


parser = argparse.ArgumentParser()
parser.add_argument(
    "--output", metavar="PNG", required=True, help="where to write the PNG file"
)
args = parser.parse_args()

# Labels and arrows are centred halfway between the middle of the x-height
# and the middle of the cap height, since the rows mix lowercase and figures.
MIDDLE = (ink_top("x", SIZE) + ink_top("H", SIZE)) / 4

newPage(WIDTH, HEIGHT)
fill(*CREAM)
rect(0, 0, WIDTH, HEIGHT)
for i, (tag, txt) in enumerate(ROWS):
    y = HEIGHT - FIRST_BASELINE - i * LINE_HEIGHT
    centred(tag, MARGIN, y + MIDDLE, 30, 500, GREY)
    glyphs(txt, DEFAULT_X, y, SIZE, WGHT, INK)
    centred("→", ARROW_X, y + MIDDLE, 48, 500, GREY)
    glyphs(txt, ALTERNATE_X, y, SIZE, WGHT, RED, tag)
saveImage(args.output)
