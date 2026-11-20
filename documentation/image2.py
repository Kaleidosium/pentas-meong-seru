# README image 2: small caps and the classic alternates.
#
# Run from the root of the repository after building the fonts:
#   python3 documentation/image2.py --output documentation/image2.png
# `make images` runs every documentation/image*.py this way.
import argparse

from drawbot_skia.drawbot import *

FONT = "fonts/variable/PentasMeongSeru[wght].ttf"
WIDTH, HEIGHT, MARGIN = 1600, 820, 80
# Each line has a small label above it naming the features it uses.
LABEL_SIZE, LABEL_RISE = 24, 98
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


def label(txt, baseline):
    """Labels the line whose baseline is `baseline` px from the top."""
    fill(*GREY)
    font(FONT, LABEL_SIZE)
    fontVariations(wght=500)
    openTypeFeatures(resetFeatures=True)
    text(txt, (MARGIN, HEIGHT - baseline + LABEL_RISE))


parser = argparse.ArgumentParser()
parser.add_argument(
    "--output", metavar="PNG", required=True, help="where to write the PNG file"
)
args = parser.parse_args()

newPage(WIDTH, HEIGHT)
fill(*CREAM)
rect(0, 0, WIDTH, HEIGHT)
label("smcp", 211)
fill(*RED)
line("Pentas Meong! Live 2026", 211, 110, 800, "smcp", "cpsp")
label("c2sc", 381)
fill(*RED)
line("ROCK & ROLL! KUCING 19.30 WIB", 381, 110, 800, "c2sc", "cpsp")
label("default", 551)
fill(*INK)
line("KUCING, “KAPAL?” & 469", 551, 110, 800, "cpsp")
label("ss05 ss06 ss07 ss08", 721)
fill(*GREY)
line("KUCING, “KAPAL?” & 469", 721, 110, 800, "ss05", "ss06", "ss07", "ss08", "cpsp")
saveImage(args.output)
