# README image 2: small caps and the classic alternates.
#
# Run from the root of the repository after building the fonts:
#   python3 documentation/image2.py --output documentation/image2.png
# `make images` runs every documentation/image*.py this way.
import argparse

from drawbot_skia.drawbot import *

FONT = "fonts/variable/PentasMeongSeru[wght].ttf"
WIDTH, HEIGHT, MARGIN = 1600, 780, 80
CREAM = (250 / 255, 246 / 255, 224 / 255)
RED = (170 / 255, 48 / 255, 44 / 255)
INK = (25 / 255, 25 / 255, 25 / 255)
GREY = (120 / 255, 120 / 255, 120 / 255)


def line(txt, baseline, size, wght, *features):
    """Draws one line of text with its baseline `baseline` px from the top."""
    font(FONT, size)
    fontVariations(wght=wght)
    openTypeFeatures(resetFeatures=True, **{tag: True for tag in features})
    text(txt, (MARGIN, HEIGHT - baseline))


parser = argparse.ArgumentParser()
parser.add_argument(
    "--output", metavar="PNG", required=True, help="where to write the PNG file"
)
args = parser.parse_args()

newPage(WIDTH, HEIGHT)
fill(*CREAM)
rect(0, 0, WIDTH, HEIGHT)
fill(*RED)
line("Pentas Meong! Live 2026", 171, 110, 800, "smcp", "cpsp")  # small caps
line("ROCK & ROLL! KUCING 7.30 PM", 341, 110, 600, "c2sc", "cpsp")  # all small caps
fill(*INK)
line('KUCING, "KAPAL" & KOPI 4', 511, 110, 800, "cpsp")  # default forms
fill(*GREY)
line(
    'KUCING, "KAPAL" & KOPI 4', 681, 110, 800, "ss05", "ss06", "ss07", "ss08", "cpsp"
)  # classic forms
saveImage(args.output)
