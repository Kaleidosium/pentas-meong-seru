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

The static WOFF2 webfonts are regenerated from the re-hinted TTFs. The variable
font stays unhinted, as Google Fonts requires.

Usage: python3 scripts/rehint.py fonts
"""

import glob
import os
import sys

from fontTools.ttLib import TTFont
from ttfautohint import ttfautohint
from ttfautohint.options import parse_args

TTFA_ARGS = [
    "--hinting-range-min=12",
    "--hinting-range-max=32",
    "--hinting-limit=32",
    "--x-height-snapping-exceptions=12-14",
    "--stem-width-mode=sss",
]


def main(fonts_dir):
    ttfs = sorted(glob.glob(os.path.join(fonts_dir, "ttf", "*.ttf")))
    for path in ttfs:
        tmp = path + ".rehint"
        ttfautohint(**parse_args([path, tmp, *TTFA_ARGS]))
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
        "Re-hinted %d static TTFs (ttfautohint %s) and rebuilt %d static WOFF2 files"
        % (len(ttfs), " ".join(TTFA_ARGS), webfonts)
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fonts")
