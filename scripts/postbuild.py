#!/usr/bin/env python3
"""Post-build fixes for every built font (run by `make build` after rehint.py).

1. Unique ID (name ID 3): removes the empty vendor field that gftools leaves,
   which otherwise shows as a run of spaces ("1.000;    ;PentasMeongSeru-Regular").
2. OS/2 fsSelection: sets the WWS bit. Each family only varies in weight, so
   its names are WWS-conformant.
3. meta table: declares that the fonts are designed for, and support, Latin
   (dlng and slng = Latn).
4. CFF names (OTF): copies the PostScript, full and family names from the name
   table into the CFF table. gftools renames the SC family in the name table
   only, so the SC OTFs kept the main family's CFF names (PentasMeongSeru-Bold),
   and apps that identify fonts by them could confuse the two families.
5. SC family: drops the smcp feature. gftools builds "Pentas Meong Seru SC" by
   copying the smcp lookups into ccmp, so its lowercase is already small caps
   and smcp has nothing left to do (QA tools then report every letter as "smcp
   had no effect"). c2sc stays, for all-small-caps text.

Usage: python3 scripts/postbuild.py fonts/
"""
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont, newTable

WWS_BIT = 1 << 8
META = {"dlng": "Latn", "slng": "Latn"}


def drop_feature(font, tag):
    """Remove every FeatureRecord with this tag from GSUB and re-index references."""
    if "GSUB" not in font or not font["GSUB"].table.FeatureList:
        return False
    table = font["GSUB"].table
    records = table.FeatureList.FeatureRecord
    keep = [i for i, rec in enumerate(records) if rec.FeatureTag != tag]
    if len(keep) == len(records):
        return False
    remap = {old: new for new, old in enumerate(keep)}
    table.FeatureList.FeatureRecord = [records[i] for i in keep]
    table.FeatureList.FeatureCount = len(keep)
    for script in table.ScriptList.ScriptRecord:
        langsys = [script.Script.DefaultLangSys] if script.Script.DefaultLangSys else []
        langsys += [rec.LangSys for rec in script.Script.LangSysRecord]
        for ls in langsys:
            ls.FeatureIndex = [remap[i] for i in ls.FeatureIndex if i in remap]
            ls.FeatureCount = len(ls.FeatureIndex)
            if ls.ReqFeatureIndex != 0xFFFF:
                ls.ReqFeatureIndex = remap.get(ls.ReqFeatureIndex, 0xFFFF)
    variations = getattr(table, "FeatureVariations", None)
    if variations:
        for rec in variations.FeatureVariationRecord:
            subst = rec.FeatureTableSubstitution
            subst.SubstitutionRecord = [s for s in subst.SubstitutionRecord if s.FeatureIndex in remap]
            for s in subst.SubstitutionRecord:
                s.FeatureIndex = remap[s.FeatureIndex]
            subst.SubstitutionCount = len(subst.SubstitutionRecord)
    return True


def fix_font(path):
    font = TTFont(path)
    changed = False
    for rec in font["name"].names:
        if rec.nameID == 3:
            old = rec.toUnicode()
            new = re.sub(r";\s*;", ";", old)
            if new != old:
                rec.string = new
                changed = True
    os2 = font["OS/2"]
    if os2.version >= 4 and not os2.fsSelection & WWS_BIT:
        os2.fsSelection |= WWS_BIT
        changed = True
    if "meta" not in font or font["meta"].data != META:
        meta = newTable("meta")
        meta.data = dict(META)
        font["meta"] = meta
        changed = True
    if "CFF " in font:
        name = font["name"]
        cff = font["CFF "].cff
        top = cff.topDictIndex[0]
        wanted = {
            "FullName": name.getDebugName(4),
            "FamilyName": name.getDebugName(16) or name.getDebugName(1),
        }
        ps = name.getDebugName(6)
        if cff.fontNames != [ps]:
            cff.fontNames = [ps]
            changed = True
        for key, value in wanted.items():
            if value and getattr(top, key, None) != value:
                setattr(top, key, value)
                changed = True
    if "SeruSC" in Path(path).name and drop_feature(font, "smcp"):
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
    print(f"postbuild: {count} font(s) updated")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fonts")
