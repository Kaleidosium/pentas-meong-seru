#!/usr/bin/env python3
"""Post-build fixes for every built font (run by `make build`).

1. PostScript names: the family name "Pentas Meong!" contains "!", which
   gftools copies into the PostScript names of the variable fonts and the
   small-caps (SC) family (e.g. "PentasMeong!-Regular"). The static fonts
   already use the slug from the Glyphs source ("PentasMeongSeru-Regular"), so
   this script makes all outputs consistent: name IDs 3 (unique ID), 6 and 25,
   fvar instance PostScript names, and the CFF font name of OTFs.
2. Unique ID (name ID 3): removes the empty vendor field, which otherwise
   leaves a run of spaces ("1.000;    ;PentasMeongSeru-Regular").
3. OS/2 fsSelection: sets the WWS bit. Each family only varies in weight,
   so its names are WWS-conformant.

Usage: python3 scripts/fix-ps-names.py fonts/
"""
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

SLUGS = [("PentasMeong!SC", "PentasMeongSeruSC"), ("PentasMeong!", "PentasMeongSeru")]
WWS_BIT = 1 << 8


def fix(text):
    for old, new in SLUGS:
        if old in text:
            return text.replace(old, new)
    return text


def fix_font(path):
    font = TTFont(path)
    name = font["name"]
    ids = {3, 6, 25}
    if "fvar" in font:
        ids |= {i.postscriptNameID for i in font["fvar"].instances if i.postscriptNameID not in (None, 0xFFFF)}
    changed = False
    for rec in name.names:
        if rec.nameID in ids:
            old = rec.toUnicode()
            new = fix(old)
            if rec.nameID == 3:
                new = re.sub(r";\s*;", ";", new)
            if new != old:
                rec.string = new
                changed = True
    if "CFF " in font:
        cff = font["CFF "].cff
        new_names = [fix(n) for n in cff.fontNames]
        if new_names != cff.fontNames:
            cff.fontNames = new_names
            changed = True
    os2 = font["OS/2"]
    if os2.version >= 4 and not os2.fsSelection & WWS_BIT:
        os2.fsSelection |= WWS_BIT
        changed = True
    if changed:
        font.save(path)
    return changed


def main(root):
    count = 0
    for path in sorted(Path(root).rglob("*")):
        if path.suffix.lower() in (".ttf", ".otf", ".woff2"):
            if fix_font(str(path)):
                count += 1
                print("fixed", path)
    print(f"{count} font(s) updated")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fonts")
