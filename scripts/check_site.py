#!/usr/bin/env python3
"""Fail-closed site contract for GEMSDOE83 (rewritten 2026-10-21).

Passes ONLY if: unified run card designates exactly one primary whose
-zeros.tif exists under docs/downloads, its checks-*.json receipt exists
and strict_finite_passed is true, the negative H83-F candidate is labelled
DO NOT SUBMIT on the home page, the submission note is <=140 chars, and
every local link in docs/*.html resolves inside docs/. No data/ needed.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("href", "src") and v: self.links.append(v)

def main():
    card = json.loads((DOCS / "run-card.json").read_text())
    ev = json.loads((ROOT / "evidence/run_card.json").read_text())
    assert card == ev, "docs/run-card.json and evidence/run_card.json must be identical"
    assert card["verdict"] in ("promote", "negative")
    note = card["submission_note"]; assert note and len(note) <= 140, len(note or "")
    primary = DOCS / "downloads" / card["submission_file"]
    assert primary.exists(), f"primary missing: {primary}"
    receipt = json.loads((DOCS / "downloads" / f"checks-{card['submission_file']}.json").read_text())
    assert receipt["strict_finite_passed"] is True, "primary receipt must pass strict-finite"
    assert receipt["sha256"] == card["raster_sha256"], "run-card sha must match receipt"
    assert card["validator_output"]["passed"] is True
    assert card["validator_output"]["no_nan_inside_footprint"] is True
    home = (DOCS / "index.html").read_text()
    assert card["submission_file"] in home, "primary download must be on home page"
    assert "DO NOT SUBMIT" in home, "negative candidate must be visibly gated"
    for f in sorted(DOCS.glob("*.html")):
        text = f.read_text(); assert '<html lang="en">' in text, f.name
        parser = Links(); parser.feed(text)
        for link in parser.links:
            u = urlsplit(link)
            if u.scheme or u.netloc or not u.path: continue
            target = (f.parent / unquote(u.path)).resolve()
            assert target.is_relative_to(DOCS.resolve()), f"link escapes site: {f.name}: {link}"
            assert target.exists(), f"broken link in {f.name}: {link}"
    landing = (ROOT / "index.html").read_text()
    assert "url=docs/index.html" in landing
    print("PASS: unified run card, strict-valid primary + receipt, negative gated, all local links resolve")

if __name__ == "__main__":
    main()
