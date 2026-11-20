# README image 4: running text, with the default contextual alternates
# (raised colons, ×, →).
#
# Run from the root of the repository after building the fonts:
#   python3 documentation/image4.py --output documentation/image4.png
# `make images` runs every documentation/image*.py this way.
import argparse

from drawbot_skia.drawbot import *

FONT = "fonts/variable/PentasMeongSeru[wght].ttf"
WIDTH, HEIGHT, MARGIN = 1600, 346, 80
PAPER = (250 / 255, 248 / 255, 240 / 255)
INK = (25 / 255, 25 / 255, 25 / 255)
LINES = [
    "Pentas Meong! started on gig posters, but it is just as happy setting the",
    "small print underneath: line-ups, set times and ticket prices. Doors open",
    "18:30, the band plays 19:30–22:00 (VIP area: 3x4 m, upstairs -> left).",
    "Tickets 75k at the door. “Kok bisa semurah itu?”",
]
SIZE, FIRST_BASELINE, LINE_HEIGHT = 40, 104, 58

parser = argparse.ArgumentParser()
parser.add_argument(
    "--output", metavar="PNG", required=True, help="where to write the PNG file"
)
args = parser.parse_args()

newPage(WIDTH, HEIGHT)
fill(*PAPER)
rect(0, 0, WIDTH, HEIGHT)
fill(*INK)
font(FONT, SIZE)
fontVariations(wght=400)
for i, txt in enumerate(LINES):
    text(txt, (MARGIN, HEIGHT - FIRST_BASELINE - i * LINE_HEIGHT))
saveImage(args.output)
