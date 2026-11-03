#!/usr/bin/env python3
"""Give every built font the ASCII PostScript slug "PentasMeongSeru".

The family name "Pentas Meong!" contains "!", which gftools copies into the
PostScript names of the variable fonts and the small-caps (SC) family
(e.g. "PentasMeong!-Regular"). The static fonts already use the slug from the
Glyphs source ("PentasMeongSeru-Regular"), so this script makes all outputs
consistent: name IDs 3 (unique ID), 6 and 25, fvar instance PostScript names,
and the CFF font name of OTFs.

Usage: python3 scripts/fix-ps-names.py fonts/
"""
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

SLUGS = [("PentasMeong!SC", "PentasMeongSeruSC"), ("PentasMeong!", "PentasMeongSeru")]


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
            if new != old:
                rec.string = new
                changed = True
    if "CFF " in font:
        cff = font["CFF "].cff
        new_names = [fix(n) for n in cff.fontNames]
        if new_names != cff.fontNames:
            cff.fontNames = new_names
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
