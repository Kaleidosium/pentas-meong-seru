# README image 6: the name and the signature shapes, at the 760 x 506 px size
# the Google Fonts README guide asks for.
#
# Run from the root of the repository after building the fonts:
#   python3 documentation/image6.py --output documentation/image6.png
# `make images` runs every documentation/image*.py this way.
import argparse

from drawbot_skia.drawbot import *

FONT = "fonts/variable/PentasMeongSeru[wght].ttf"
# The row of shapes is measured by its ink, and BezierPath can't set a weight,
# so that row uses the static Black font for both measuring and drawing.
BLACK = "fonts/ttf/PentasMeongSeru-Black.ttf"
WIDTH, HEIGHT, MARGIN = 760, 506, 48
CREAM = (250 / 255, 246 / 255, 224 / 255)
RED = (170 / 255, 48 / 255, 44 / 255)
INK = (25 / 255, 25 / 255, 25 / 255)
GREY = (120 / 255, 120 / 255, 120 / 255)


def line(txt, baseline, size, wght, color, *features):
    """Draws one line of text with its baseline `baseline` px from the top."""
    fill(*color)
    font(FONT, size)
    fontVariations(wght=wght)
    openTypeFeatures(resetFeatures=True, **{tag: True for tag in features})
    text(txt, (MARGIN, HEIGHT - baseline))


def spread(glyphs, baseline, size, color):
    """Draws `glyphs` in Black across the margins, with equal gaps between
    their ink."""
    paths = []
    for glyph in glyphs:
        path = BezierPath()
        path.text(glyph, font=BLACK, fontSize=size)
        paths.append(path.bounds())
    ink = sum(right - left for left, _, right, _ in paths)
    gap = (WIDTH - 2 * MARGIN - ink) / (len(glyphs) - 1)
    x = MARGIN
    fill(*color)
    font(BLACK, size)
    openTypeFeatures(resetFeatures=True)
    for glyph, (left, _, right, _) in zip(glyphs, paths):
        text(glyph, (x - left, HEIGHT - baseline))
        x += right - left + gap


parser = argparse.ArgumentParser()
parser.add_argument(
    "--output", metavar="PNG", required=True, help="where to write the PNG file"
)
args = parser.parse_args()

newPage(WIDTH, HEIGHT)
fill(*CREAM)
rect(0, 0, WIDTH, HEIGHT)
line("Pentas Meong!", 118, 84, 900, INK)
spread("K4&*,”?", 322, 160, RED)
line("Eight weights, true small caps, Latin and Vietnamese", 440, 25, 500, GREY)
saveImage(args.output)
