# README image 3: the eight weights.
#
# Run from the root of the repository after building the fonts:
#   python3 documentation/image3.py --output documentation/image3.png
# `make images` runs every documentation/image*.py this way.
import argparse

from drawbot_skia.drawbot import *

FONT = "fonts/variable/PentasMeongSeru[wght].ttf"
WIDTH, HEIGHT, MARGIN = 1600, 1284, 80
PAPER = (250 / 255, 248 / 255, 240 / 255)
INK = (25 / 255, 25 / 255, 25 / 255)
WEIGHTS = [
    ("ExtraLight", 200),
    ("Light", 300),
    ("Regular", 400),
    ("Medium", 500),
    ("SemiBold", 600),
    ("Bold", 700),
    ("ExtraBold", 800),
    ("Black", 900),
]
SIZE, FIRST_BASELINE, LINE_HEIGHT = 96, 156, 148

parser = argparse.ArgumentParser()
parser.add_argument("--output", metavar="PNG", required=True, help="where to write the PNG file")
args = parser.parse_args()

newPage(WIDTH, HEIGHT)
fill(*PAPER)
rect(0, 0, WIDTH, HEIGHT)
fill(*INK)
for i, (name, wght) in enumerate(WEIGHTS):
    font(FONT, SIZE)
    fontVariations(wght=wght)
    text(f"{name} Kucing kecil, kapal besar", (MARGIN, HEIGHT - FIRST_BASELINE - i * LINE_HEIGHT))
saveImage(args.output)
