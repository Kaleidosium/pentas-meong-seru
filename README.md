# Pentas Meong!

![Pentas Meong!](documentation/image1.png)

**Pentas Meong!** is a quirky condensed sans for posters, websites and music and art
headlines that still holds up in running text. It pairs heavy, condensed capitals
with true small caps, a curved-arm **K**, and wedge-shaped commas and quotes. The
family has eight weights from ExtraLight to Black, as a variable font and as
statics.

Pentas Meong! was inspired by the text face of Lomba Sihir's album _Obrolan Jam
3 Pagi_: the typeface used for its lyrics and other text, alongside the album's
fantail display lettering.

It is derived from [Reddit Sans Condensed](https://github.com/reddit/redditsans) by
Stephen Hutchings / Reddit, Inc., released under the SIL Open Font License.

## Features

![Small caps and alternates](documentation/image2.png)

| Feature                                         | What it does                                                                                              |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `smcp`                                          | Lowercase → small caps (incl. all accented letters)                                                       |
| `c2sc`                                          | Capitals → small caps; also small-cap figures and `& ! ? ¡ ¿`                                             |
| `cpsp`                                          | Poster tracking for capitals and small caps (scales with weight: +16 to +40 units per side)               |
| `ss05` "Straight K"                             | The classic straight-armed K / k                                                                          |
| `ss06` "Classic punctuation"                    | The classic round comma, semicolon and quotes                                                             |
| `ss01`–`ss04`, `cv01`–`cv18`                    | Alternates inherited from Reddit Sans (single-storey a, two-storey g, barred I, tall W, circular zero, …) |
| `tnum`, `onum`, `frac`, `case`, `sups`/`subs` … | Figure styles and other features inherited from Reddit Sans                                               |

The build also produces **Pentas Meong! SC**, a separate family in which the
lowercase _is_ small caps by default. Use it in apps that can't switch OpenType
features on.

![Weights](documentation/image3.png)

### On the web

```css
@font-face {
  font-family: "Pentas Meong!";
  src: url("fonts/webfonts/PentasMeongSeru[wght].woff2") format("woff2");
  font-weight: 200 900;
}

.poster {
  font-family: "Pentas Meong!";
  font-weight: 820;
  font-feature-settings: "cpsp";
}
.title {
  font-variant-caps: small-caps;
} /* smcp */
.label {
  font-variant-caps: all-small-caps;
} /* smcp + c2sc */
.classic {
  font-feature-settings: "ss05", "ss06";
}
```

![Text](documentation/image4.png)

## Fonts

| Folder                     | Contents                                                   |
| -------------------------- | ---------------------------------------------------------- |
| `fonts/variable/`          | `PentasMeongSeru[wght].ttf`, `PentasMeongSeruSC[wght].ttf` |
| `fonts/ttf/`, `fonts/otf/` | Static fonts, ExtraLight–Black, plus the SC family         |
| `fonts/webfonts/`          | WOFF2 (variable and static)                                |

PostScript and file names use the ASCII slug **PentasMeongSeru** ("seru" is the
Indonesian word for "!"). The family name shown in menus is "Pentas Meong!".

## Building

This repository follows the [Google Fonts project
template](https://github.com/googlefonts/googlefonts-project-template). GitHub
Actions builds the fonts on every push, runs fontspector QA, publishes proofs to
GitHub Pages, and attaches a zip to every tagged release.

To build locally (Python 3.10+):

```sh
make build   # creates a venv, runs gftools builder, writes fonts/
make test    # QA with fontspector (needs `cargo binstall fontspector`)
make proof   # HTML proofs with diffenator3
```

The source is `sources/PentasMeongSeru.glyphs` (Glyphs 4). The build is
configured in `sources/config.yaml`. `scripts/fix-ps-names.py` runs after the
build so every output uses the `PentasMeongSeru` PostScript names.

To show proofs and QA reports on GitHub Pages, open **Settings → Pages** and set
**Source** to **GitHub Actions**.

## Credits

- Pentas Meong! (2026): The Pentas Meong! Project Authors (see `AUTHORS.txt`)
- Original design: [Reddit Sans](https://github.com/reddit/redditsans) by Stephen
  Hutchings for Reddit, Inc.

## License

Copyright 2026 The Pentas Meong! Project Authors.
Copyright 2020-2023 Reddit, Inc. (<https://github.com/reddit/redditsans>).

This Font Software is licensed under the SIL Open Font License, Version 1.1.
See [OFL.txt](OFL.txt). The license is also available with a FAQ at
<https://openfontlicense.org>.
