# README image 1: the "Pentas Meong!" poster.
#
# Run from the root of the repository after building the fonts:
#   python3 documentation/image1.py --output documentation/image1.png
# `make images` runs every documentation/image*.py this way.
import argparse

from drawbot_skia.drawbot import *

FONT = "fonts/variable/PentasMeongSeru[wght].ttf"
WIDTH, HEIGHT, MARGIN = 1600, 953, 80
# The headline starts further left so its ink lines up with the subtitle's.
HEADLINE_X = 64
RED = (170 / 255, 48 / 255, 44 / 255)
CREAM = (250 / 255, 246 / 255, 224 / 255)


def line(txt, baseline, size, wght, *features, x=MARGIN):
    """Draws one line of text with its baseline `baseline` px from the top."""
    font(FONT, size)
    fontVariations(wght=wght)
    openTypeFeatures(resetFeatures=True, **{tag: True for tag in features})
    text(txt, (x, HEIGHT - baseline))


parser = argparse.ArgumentParser()
parser.add_argument(
    "--output", metavar="PNG", required=True, help="where to write the PNG file"
)
args = parser.parse_args()

newPage(WIDTH, HEIGHT)
fill(*RED)
rect(0, 0, WIDTH, HEIGHT)
fill(*CREAM)
line("PENTAS", 320, 300, 900, "cpsp", x=HEADLINE_X)
line("MEONG!", 620, 300, 900, "cpsp", x=HEADLINE_X)
line("MUSIK, SENI & KUCING: LIVE 2026", 861, 95, 760, "cpsp")
saveImage(args.output)
