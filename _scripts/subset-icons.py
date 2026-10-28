#!/usr/bin/env python3
"""Build assets/css/icons.css: just the Font Awesome rules this page uses.

The full Font Awesome stylesheet (assets/css/all.min.css, kept as the source
and not published) is about 75 KB, but the page only shows a few dozen icons.

Run it again after adding or changing an icon in _config.yml or index.html:

    python3 _scripts/subset-icons.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets/css/all.min.css"
OUTPUT = ROOT / "assets/css/icons.css"

# Style classes, not icons.
STYLE_CLASSES = {"fa", "fas", "far", "fab", "fa-solid", "fa-regular", "fa-brands", "fa-classic"}
# Rules for these classes set up fonts and variables, so they are always kept.
BASE_RE = r"(?<![\w-])(?:\.(?:%s)|:root|:host)(?![\w-])" % "|".join(re.escape(c) for c in STYLE_CLASSES)
# Only the solid and brands fonts are used.
FONTS = ('"Font Awesome 7 Brands"', '"Font Awesome 7 Free";font-style:normal;font-weight:900')


def used_icons():
    text = (ROOT / "_config.yml").read_text() + (ROOT / "index.html").read_text()
    names = set(re.findall(r"\bfa-[a-z0-9-]+", text))
    return {n for n in names if n not in STYLE_CLASSES}


def split_top_level(css):
    """Yield each top-level rule or comment, with its nested blocks intact."""
    i = 0
    while i < len(css):
        if css.startswith("/*", i):
            end = css.index("*/", i) + 2
            yield css[i:end]
            i = end
            continue
        depth, j = 0, i
        while j < len(css):
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        yield css[i:j + 1]
        i = j + 1


def split_selectors(selectors):
    """Split on commas that aren't inside brackets, e.g. :is(.a,.b)."""
    parts, depth, cur = [], 0, ""
    for ch in selectors:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return parts + [cur]


def main():
    icons = used_icons()
    found, out = set(), []
    for rule in split_top_level(SOURCE.read_text()):
        rule = rule.strip()
        if not rule:
            continue
        if rule.startswith("/*!"):
            out.append(rule)  # licence
        elif rule.startswith("@font-face"):
            if any(f in rule for f in FONTS):
                out.append(rule)
        elif rule.startswith("@supports"):
            if ":before{content:var(--fa)}" in rule:
                out.append(rule)
        elif rule.startswith("@") or rule.startswith("/*"):
            continue  # animations, media queries, other comments
        else:
            selectors, body = rule.split("{", 1)
            parts = split_selectors(selectors)
            if '--fa:"' in body:
                keep = [s for s in parts if s.lstrip(".") in icons]
                found.update(s.lstrip(".") for s in keep)
                if keep:
                    out.append(",".join(keep) + "{" + body)
            elif re.search(BASE_RE, selectors):
                out.append(rule)
    missing = sorted(icons - found)
    if missing:
        raise SystemExit("Not in Font Awesome: " + ", ".join(missing))
    OUTPUT.write_text("\n".join(out) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(found)} icons, {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
