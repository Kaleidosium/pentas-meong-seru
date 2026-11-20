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
   and apps that identify fonts by them could confuse the two families. The
   copyright string is copied too, because the builder strips brackets and
   slashes from the CFF copy, which mangles the URLs in it.
5. SC family: drops the smcp and c2sc features. gftools builds "Pentas Meong
   Seru SC" by copying the smcp lookups into ccmp, so its lowercase is already
   small caps and smcp can't change anything (fontspector's shape_languages
   warns about that). Dropping smcp alone isn't enough: while c2sc is there,
   missing_small_caps_glyphs expects smcp to cover every lowercase letter and
   FAILs. Without both, all-small-caps text needs the main family's smcp+c2sc.
6. cpsp (static fonts): the tracking values are per-master number values, and
   the static instances all get the Regular master's. Each static font gets
   the value the variable font has at its weight, so cpsp scales there too.
7. TrueType fonts: sets the overlap flag on the glyphs that overlap and clears
   it on the rest. The variable fonts keep their contours' overlaps, and in
   the static fonts composites such as Ą, Ç and Ơ still overlap where their
   components meet. Some renderers need the flag to fill them without seams.
   fontspector's overlaps_bit check warns about a flag on a glyph that doesn't
   overlap as well as a missing one.
8. Variable WOFF2: rebuilt from the finished variable TTF. gftools compresses
   it before the STAT table is generated, so it would otherwise ship with an
   empty STAT.
9. SC family: points the character map straight at the small caps, so apps
   that don't apply ccmp still get them. A first ccmp lookup maps them back to
   the lowercase glyphs, so shaping apps take exactly the path gftools built:
   locl, ordn and the other lowercase rules run, then the copied smcp lookups
   turn the result into small caps.
10. GSUB: drops the grek script. The source registers the features for grek
   so that pi and the Ohm sign get cpsp and marks in GPOS, which keeps its
   grek script. In GSUB it adds nothing (shapers fall back to DFLT, which has
   the same lookups), and it makes ttfautohint hint every alternate glyph with
   Greek alignment zones. rehint.py does this for the static TTFs before it
   hints them.
11. OS/2 usWeightClass (static OTF): ExtraLight is 275 instead of 200. Older
   Windows applications embolden CFF fonts lighter than 250, so Google Fonts
   asks for 275 there.

Usage: python3 scripts/postbuild.py fonts/
"""

import re
import sys
from collections import Counter
from pathlib import Path

import pathops
from fontTools.misc.fixedTools import otRound
from fontTools.otlLib import builder as otl
from fontTools.pens.areaPen import AreaPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import OVERLAP_COMPOUND, flagOverlapSimple
from fontTools.varLib.models import normalizeValue, piecewiseLinearMap
from fontTools.varLib.varStore import VarStoreInstancer

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
            subst.SubstitutionRecord = [
                s for s in subst.SubstitutionRecord if s.FeatureIndex in remap
            ]
            for s in subst.SubstitutionRecord:
                s.FeatureIndex = remap[s.FeatureIndex]
            subst.SubstitutionCount = len(subst.SubstitutionRecord)
    return True


def drop_gsub_script(font, tag):
    """Remove a script from GSUB. Its lookups stay; shapers fall back to DFLT."""
    if "GSUB" not in font or not font["GSUB"].table.ScriptList:
        return False
    scripts = font["GSUB"].table.ScriptList
    keep = [rec for rec in scripts.ScriptRecord if rec.ScriptTag != tag]
    if len(keep) == len(scripts.ScriptRecord):
        return False
    scripts.ScriptRecord = keep
    scripts.ScriptCount = len(keep)
    return True


def nested_lookup_records(subtable):
    """Every SubstLookupRecord of a contextual GSUB subtable, in any format."""
    yield from getattr(subtable, "SubstLookupRecord", None) or []
    for set_attr, rule_attr in (
        ("SubRuleSet", "SubRule"),
        ("SubClassSet", "SubClassRule"),
        ("ChainSubRuleSet", "ChainSubRule"),
        ("ChainSubClassSet", "ChainSubClassRule"),
    ):
        for rule_set in getattr(subtable, set_attr, None) or []:
            for rule in (getattr(rule_set, rule_attr, None) if rule_set else None) or []:
                yield from rule.SubstLookupRecord


def shift_gsub_lookup_indices(table, by):
    """Add `by` to every reference to a GSUB lookup."""
    features = [rec.Feature for rec in table.FeatureList.FeatureRecord]
    variations = getattr(table, "FeatureVariations", None)
    if variations:
        for rec in variations.FeatureVariationRecord:
            features += [
                s.Feature for s in rec.FeatureTableSubstitution.SubstitutionRecord
            ]
    for feature in {id(f): f for f in features}.values():
        feature.LookupListIndex = [i + by for i in feature.LookupListIndex]
    for lookup in table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            subtable = getattr(subtable, "ExtSubTable", subtable)
            for record in nested_lookup_records(subtable):
                record.LookupListIndex += by


def single_substitutions(font, tag):
    """The combined mapping of the single-substitution lookups of a GSUB feature."""
    table = font["GSUB"].table
    mapping = {}
    indices = {
        index
        for rec in table.FeatureList.FeatureRecord
        if rec.FeatureTag == tag
        for index in rec.Feature.LookupListIndex
    }
    for index in sorted(indices):
        for subtable in table.LookupList.Lookup[index].SubTable:
            subtable = getattr(subtable, "ExtSubTable", subtable)
            if subtable.LookupType == 1:
                mapping.update(subtable.mapping)
    return mapping


def map_lowercase_to_small_caps(font):
    """Encode the SC family's small caps directly, keeping shaping unchanged."""
    if "GSUB" not in font:
        return False
    smcp = single_substitutions(font, "smcp")
    encoded = set(font.getBestCmap().values())
    forward = {glyph: smcp[glyph] for glyph in encoded if glyph in smcp}
    # The way back has to be unambiguous.
    uses = Counter(forward.values())
    forward = {glyph: sc for glyph, sc in forward.items() if uses[sc] == 1}
    if not forward:
        return False
    for subtable in font["cmap"].tables:
        if subtable.isUnicode():
            subtable.cmap = {
                code: forward.get(glyph, glyph) for code, glyph in subtable.cmap.items()
            }
    table = font["GSUB"].table
    back = otl.buildSingleSubstSubtable({sc: glyph for glyph, sc in forward.items()})
    shift_gsub_lookup_indices(table, 1)
    table.LookupList.Lookup.insert(0, otl.buildLookup([back]))
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    for rec in table.FeatureList.FeatureRecord:
        if rec.FeatureTag == "ccmp":
            rec.Feature.LookupListIndex.insert(0, 0)
            rec.Feature.LookupCount = len(rec.Feature.LookupListIndex)
    return True


def feature_value_records(font, tag):
    """Every ValueRecord in the single-adjustment lookups of a GPOS feature."""
    if "GPOS" not in font:
        return []
    table = font["GPOS"].table
    indices = {
        index
        for rec in table.FeatureList.FeatureRecord
        if rec.FeatureTag == tag
        for index in rec.Feature.LookupListIndex
    }
    records = []
    for index in sorted(indices):
        for sub in table.LookupList.Lookup[index].SubTable:
            sub = getattr(sub, "ExtSubTable", sub)
            if sub.LookupType == 1:
                records += [sub.Value] if sub.Format == 1 else list(sub.Value)
    return records


def cpsp_values_at(variable_font, wght):
    """Map each default cpsp value of a variable font to its value at wght."""
    axes = variable_font["fvar"].axes
    axis = next(a for a in axes if a.axisTag == "wght")
    coord = normalizeValue(wght, (axis.minValue, axis.defaultValue, axis.maxValue))
    coord = piecewiseLinearMap(coord, variable_font["avar"].segments["wght"])
    deltas = VarStoreInstancer(
        variable_font["GDEF"].table.VarStore, axes, {"wght": coord}
    )
    values = {}
    for rec in feature_value_records(variable_font, "cpsp"):
        for attr, device_attr in (
            ("XPlacement", "XPlaDevice"),
            ("XAdvance", "XAdvDevice"),
        ):
            device = getattr(rec, device_attr, None)
            if device is not None:
                value = getattr(rec, attr)
                index = (device.StartSize << 16) + device.EndSize
                values[value] = otRound(value + deltas[index])
    return values


def scale_static_cpsp(font, variable_font):
    """Give a static font the cpsp values the variable font has at its weight."""
    records = feature_value_records(font, "cpsp")
    values = cpsp_values_at(variable_font, font["OS/2"].usWeightClass)
    present = {
        getattr(rec, attr)
        for rec in records
        for attr in ("XPlacement", "XAdvance")
        if getattr(rec, attr, 0)
    }
    if present != set(values) or all(old == new for old, new in values.items()):
        return False
    seen = set()
    for rec in records:
        if id(rec) in seen:
            continue
        seen.add(id(rec))
        for attr in ("XPlacement", "XAdvance"):
            if getattr(rec, attr, 0):
                setattr(rec, attr, values[getattr(rec, attr)])
    return True


def variable_font_for(path, root, cache={}):
    """The built variable font of the same family as a static font."""
    pattern = "*SC*.ttf" if "SeruSC" in Path(path).name else "*Seru[[]wght].ttf"
    if pattern not in cache:
        cache[pattern] = TTFont(next((Path(root) / "variable").glob(pattern)))
    return cache[pattern]


def has_overlap(glyphset, name):
    """Whether the glyph's contours overlap, with its components drawn in.

    Overlapping contours (wound the same way) cover some area twice. The
    nonzero fill counts that area and the even-odd fill doesn't, so their
    areas differ, which is fontspector's test as well.
    """
    path = pathops.Path()
    glyphset[name].draw(path.getPen(glyphSet=glyphset))
    areas = []
    for fill in (pathops.FillType.WINDING, pathops.FillType.EVEN_ODD):
        filled = pathops.Path(path)
        filled.fillType = fill
        pen = AreaPen()
        pathops.simplify(filled).draw(pen)
        areas.append(abs(pen.value))
    # Glyphs that don't overlap measure exactly 0. The smallest real overlap,
    # 0.05 unit², is a loop that overlap removal and rounding leave in the
    # static ExtraBold þ. fontspector counts it, so only float noise is ignored.
    return areas[0] - areas[1] > 1e-6


def set_overlap_flags(font):
    """Flag the glyphs that overlap at the default or at any gvar peak, clear the rest.

    A composite gets OVERLAP_COMPOUND (on its first component, where the spec
    wants it) when it overlaps as drawn, whether its components overlap each
    other or one of them overlaps itself.
    """
    variations = font["gvar"].variations.values() if "gvar" in font else ()
    peaks = {
        tuple(sorted((tag, peak) for tag, (_, peak, _) in tv.axes.items()))
        for glyph_variations in variations
        for tv in glyph_variations
    }
    order = font.getGlyphOrder()
    overlapping = set()
    for location in [None] + [dict(peak) for peak in peaks]:
        glyphset = font.getGlyphSet(location=location, normalized=True)
        overlapping.update(
            name for name in order if name not in overlapping and has_overlap(glyphset, name)
        )
    glyf = font["glyf"]
    changed = False
    for name in order:
        glyph = glyf[name]
        if glyph.isComposite():
            for i, component in enumerate(glyph.components):
                flags = component.flags & ~OVERLAP_COMPOUND
                if i == 0 and name in overlapping:
                    flags |= OVERLAP_COMPOUND
                changed |= flags != component.flags
                component.flags = flags
        elif glyph.numberOfContours > 0:
            flags = glyph.flags[0] & ~flagOverlapSimple
            if name in overlapping:
                flags |= flagOverlapSimple
            changed |= flags != glyph.flags[0]
            glyph.flags[0] = flags
    return changed


def fix_font(path, root):
    font = TTFont(path)
    changed = False
    if "glyf" in font and set_overlap_flags(font):
        changed = True
    if "fvar" not in font and scale_static_cpsp(font, variable_font_for(path, root)):
        changed = True
    if drop_gsub_script(font, "grek"):
        changed = True
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
    # After scale_static_cpsp, which reads the weight class as the wght value.
    if "CFF " in font and os2.usWeightClass == 200:
        os2.usWeightClass = 275
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
            "Copyright": name.getDebugName(0),
        }
        ps = name.getDebugName(6)
        if cff.fontNames != [ps]:
            cff.fontNames = [ps]
            changed = True
        for key, value in wanted.items():
            if value and getattr(top, key, None) != value:
                setattr(top, key, value)
                changed = True
    if "SeruSC" in Path(path).name:
        # This reads smcp, so it has to run before the feature is dropped.
        if map_lowercase_to_small_caps(font):
            changed = True
        for tag in ("smcp", "c2sc"):
            if drop_feature(font, tag):
                changed = True
    if changed:
        font.save(path)
    return changed


def rebuild_variable_webfonts(root):
    """Compress each finished variable TTF over its WOFF2 counterpart."""
    count = 0
    for ttf in sorted((Path(root) / "variable").glob("*.ttf")):
        woff2 = Path(root) / "webfonts" / (ttf.stem + ".woff2")
        if woff2.exists():
            font = TTFont(ttf)
            font.flavor = "woff2"
            font.save(woff2)
            count += 1
    return count


def main(root):
    count = 0
    for path in sorted(Path(root).rglob("*")):
        if path.suffix.lower() in (".ttf", ".otf", ".woff2"):
            if fix_font(str(path), root):
                count += 1
    print(f"postbuild: {count} font(s) updated")
    print(f"postbuild: {rebuild_variable_webfonts(root)} variable WOFF2 rebuilt")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fonts")
