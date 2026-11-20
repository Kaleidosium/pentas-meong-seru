#!/usr/bin/env python3
"""Re-hint the static TrueType fonts with ttfautohint's strong stem-width mode.

gftools builder autohints the static TTFs with ttfautohint's defaults
("-a qsq"), which leaves the thicker horizontal strokes of the heavier weights
on fractional pixels under DirectWrite ClearType (Windows apps, browsers and
editors such as VS Code). That is what makes Bold look blurry next to Regular
(reddit/redditsans#17). "-a sss" snaps stem widths to whole pixels in every
rendering mode, so the heavier weights render crisper.

The other settings are the ones Reddit Sans uses (the "TTFAutohint options" of
every instance in the Glyphs source): hint only from 12 to 32 ppem and leave
larger sizes unhinted, and don't round the x-height up at 12 to 14 ppem.
ExtraBold and Black are the exception at 14 ppem: their x-height lands on the
next pixel there anyway, while the dots of i and j, the dieresis and the dot
of ! stay where they are and run into the letter ("Dunia!" read "Dunial").
Rounding the x-height up at 14 ppem scales the whole glyph, so the dots move
up with it (their capitals become 11 pixels tall instead of 10).

These things keep every glyph on the same pixel rows as its neighbours:

- The grek script is dropped from GSUB before hinting (postbuild.py does the
  same for the other formats). ttfautohint handles Greek before Latin and gives
  every glyph that a grek lookup can produce Greek alignment zones. The
  features are registered for grek too, so that covered every alternate
  (barred I, tabular figures, the classic 4 ...), which then came out a pixel
  taller or shorter than the capitals at many sizes.
- A control file puts the small caps in the lowercase style. They are exactly
  as tall as the x-height, but ttfautohint would give them zones of their own
  (and none to small-cap alternates such as the barred I), a pixel off the
  lowercase at some sizes.
- The same control file puts the glyphs that carry Greek code points (the
  increment sign for Delta, the Ohm sign for Omega, the micro sign for mu, pi,
  Pi, delta, omega, and M, which also stands for capital Mu) and the rupee
  sign in the Latin
  style. ttfautohint would hint the Greek ones as Greek and leave the rupee,
  which it files under Devanagari, unhinted; they then sat a pixel off the
  capitals, the lowercase and the figures.
- L caron and its small cap are decomposed first, so their vertical caron is
  hinted level with the top of the letter instead of a pixel under it (see
  decompose_lowered_carons).
- The question marks have a short stem stub over the dot. At a few sizes the
  hinted stub ended on the row above the dot and ran into it, so the control
  file moves the stub's end points away from the dot by a fraction of a pixel
  at those sizes (DOT_GAP_DELTAS). At 12-13 ppem the ExtraBold and Black small
  caps have no free row for the gap and stay joined.

The static WOFF2 webfonts are regenerated from the re-hinted TTFs. The variable
font stays unhinted, as Google Fonts requires.

Usage: python3 scripts/rehint.py fonts
"""

import glob
import os
import re
import sys
import tempfile

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from ttfautohint import ttfautohint
from ttfautohint.options import parse_args

from postbuild import drop_gsub_script

TTFA_ARGS = [
    "--hinting-range-min=12",
    "--hinting-range-max=32",
    "--hinting-limit=32",
    "--x-height-snapping-exceptions=12-14",
    "--stem-width-mode=sss",
]

# Weights that round the x-height up at 14 ppem too (see the module docstring).
HEAVY_WEIGHTS = ("ExtraBold", "Black")
HEAVY_X_HEIGHT_EXCEPTIONS = "--x-height-snapping-exceptions=12-13"


def ttfautohint_args(path):
    """TTFA_ARGS, with the 14 ppem x-height exception dropped for the heaviest weights."""
    style = os.path.splitext(os.path.basename(path))[0].rsplit("-", 1)[-1]
    if style not in HEAVY_WEIGHTS:
        return TTFA_ARGS
    return [
        HEAVY_X_HEIGHT_EXCEPTIONS
        if arg.startswith("--x-height-snapping-exceptions=")
        else arg
        for arg in TTFA_ARGS
    ]


SMALL_CAP = re.compile(r"\.(sc|c2sc)(\.|$)")

# Delta (increment), Omega (Ohm), mu (micro), pi, the rupee sign, capital Mu
# (the M glyph), capital Pi, delta and omega, by code point.
LATIN_ZONES = [0x2206, 0x2126, 0x00B5, 0x03C0, 0x20B9, 0x039C, 0x03A0, 0x03B4, 0x03C9]

# Composites whose vertical caron sits level with the top of the letter.
LOWERED_CARONS = ["Lcaron", "lcaron.sc"]

# Sizes (ppem) at which the stem stub of a question mark runs into its dot, and
# how far (in pixels) its end points move away from the dot there, per font.
# Found by rendering every size with FreeType after hinting; the points are
# looked up by position (see stem_end_points), so the values stay valid while
# the outlines do.
_LIGHT = {"questiondown.c2sc": {12: 0.25}}
DOT_GAP_DELTAS = {
    "PentasMeongSeru-ExtraLight": _LIGHT,
    "PentasMeongSeru-Light": _LIGHT,
    "PentasMeongSeru-Regular": _LIGHT,
    "PentasMeongSeru-Medium": _LIGHT,
    "PentasMeongSeru-SemiBold": {
        "questiondown": {12: 0.375},
        "question.c2sc": {14: 0.25},
        "questiondown.c2sc": {12: 0.25},
    },
    "PentasMeongSeru-Bold": {"questiondown": {12: 0.375}},
    "PentasMeongSeru-ExtraBold": {
        "question": {12: 0.25},
        "questiondown": {12: 0.25},
        "uni203D": {12: 0.25},
    },
    "PentasMeongSeru-Black": {
        "questiondown": {12: 0.25},
        "question.c2sc": {16: 0.625, 17: 0.625, 18: 0.625, 19: 0.625},
        "questiondown.c2sc": {16: 0.625, 17: 0.625, 18: 0.625, 19: 0.625},
    },
    "PentasMeongSeruSC-ExtraLight": _LIGHT,
    "PentasMeongSeruSC-Light": _LIGHT,
    "PentasMeongSeruSC-Regular": _LIGHT,
    "PentasMeongSeruSC-Medium": _LIGHT,
    "PentasMeongSeruSC-SemiBold": {"question.c2sc": {14: 0.25}, "questiondown.c2sc": {12: 0.25}},
    "PentasMeongSeruSC-Bold": {"question.c2sc": {13: 0.625}, "questiondown.c2sc": {13: 0.625}},
    "PentasMeongSeruSC-ExtraBold": {
        "question": {12: 0.25},
        "questiondown": {12: 0.25, 13: 0.375},
        "uni203D": {12: 0.25},
    },
    "PentasMeongSeruSC-Black": {
        "questiondown": {12: 0.25, 13: 0.25},
        "question.c2sc": {16: 0.625, 17: 0.625, 18: 0.625, 19: 0.625, 24: 0.625},
        "questiondown.c2sc": {16: 0.625, 17: 0.625, 18: 0.625, 19: 0.625, 24: 0.625},
    },
}


def stem_end_points(font, name):
    """The on-curve points that end a question mark's stroke next to its dot.

    Returns (point indices, direction away from the dot: 1 up, -1 down). The
    dot is the contour with the smallest height; for ? the stroke ends above it
    (its lowest points), for the inverted question mark below it (its highest).
    """
    glyf = font["glyf"]
    coords, ends, flags = glyf[name].getCoordinates(glyf)
    contours, start = [], 0
    for end in ends:
        contours.append(range(start, end + 1))
        start = end + 1
    height = lambda c: max(coords[i][1] for i in c) - min(coords[i][1] for i in c)
    dot = min(contours, key=height)
    on = [i for c in contours if c is not dot for i in c if flags[i] & 1]
    dot_y = sum(coords[i][1] for i in dot) / len(dot)
    above = dot_y < sum(coords[i][1] for i in on) / len(on)
    edge = (min if above else max)(coords[i][1] for i in on)
    return [i for i in on if coords[i][1] == edge], 1 if above else -1


def dot_gap_lines(font, path):
    """Control-file delta exceptions for this font (see DOT_GAP_DELTAS)."""
    style = os.path.splitext(os.path.basename(path))[0]
    lines = []
    for name, sizes in sorted(DOT_GAP_DELTAS.get(style, {}).items()):
        # The wide forms of ss09 have the same stem stub and dot, so they get the same shifts.
        for glyph in (name, name + ".ss09"):
            if glyph not in font["glyf"].keys():
                continue
            points, direction = stem_end_points(font, glyph)
            for ppem, shift in sorted(sizes.items()):
                lines.append(
                    "%s point %s yshift %g @ %d"
                    % (glyph, ",".join(map(str, points)), direction * shift, ppem)
                )
    return lines


def decompose_lowered_carons(font):
    """Turn L caron and its small cap into plain outlines.

    Their vertical caron is a component moved down from ascender height to
    the top of the letter. ttfautohint hints a component where its own glyph
    is drawn and the composite then moves it by a rounded offset, which left
    the caron a pixel under the top of the L at about every third size. As a
    plain outline the caron is hinted in place, on the same zone as the letter.
    """
    glyf = font["glyf"]
    glyph_set = font.getGlyphSet()
    names = [n for n in LOWERED_CARONS if n in glyf and glyf[n].isComposite()]
    for name in names:
        recording = DecomposingRecordingPen(glyph_set)
        glyph_set[name].draw(recording)
        pen = TTGlyphPen(None)
        recording.replay(pen)
        glyf[name] = pen.glyph()
    return names


def prepare(path, control_path):
    """Drop grek from GSUB, decompose the lowered carons and write the control file."""
    font = TTFont(path)
    changed = drop_gsub_script(font, "grek")
    if decompose_lowered_carons(font) or changed:
        font.save(path)
    glyph_order = font.getGlyphOrder()
    small_caps = [name for name in glyph_order if SMALL_CAP.search(name)]
    cmap = font.getBestCmap()
    with open(control_path, "w") as control:
        # One line each, before the small caps: ttfautohint ignores some of
        # these names when they are appended to the long statement below.
        for codepoint in LATIN_ZONES:
            if codepoint in cmap:
                control.write("latn dflt @ " + cmap[codepoint] + "\n")
        if small_caps:
            control.write("latn dflt @ " + ", \\\n  ".join(small_caps) + "\n")
        for line in dot_gap_lines(font, path):
            control.write(line + "\n")


def main(fonts_dir):
    ttfs = sorted(glob.glob(os.path.join(fonts_dir, "ttf", "*.ttf")))
    with tempfile.TemporaryDirectory() as tmp_dir:
        control = os.path.join(tmp_dir, "control.txt")
        for path in ttfs:
            prepare(path, control)
            tmp = path + ".rehint"
            ttfautohint(
                **parse_args(
                    [path, tmp, *ttfautohint_args(path), "--control-file=" + control]
                )
            )
            os.replace(tmp, path)
    webfonts = 0
    for woff2 in sorted(glob.glob(os.path.join(fonts_dir, "webfonts", "*.woff2"))):
        ttf = os.path.join(
            fonts_dir, "ttf", os.path.basename(woff2)[: -len(".woff2")] + ".ttf"
        )
        if not os.path.exists(ttf):  # the variable webfont has no static counterpart
            continue
        font = TTFont(ttf)
        font.flavor = "woff2"
        font.save(woff2)
        webfonts += 1
    print(
        "Re-hinted %d static TTFs (ttfautohint %s; %s for %s) and rebuilt %d static"
        " WOFF2 files"
        % (
            len(ttfs),
            " ".join(TTFA_ARGS),
            HEAVY_X_HEIGHT_EXCEPTIONS,
            " and ".join(HEAVY_WEIGHTS),
            webfonts,
        )
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fonts")
