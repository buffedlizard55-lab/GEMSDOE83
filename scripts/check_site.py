"""Check every local HTML target and the fail-closed status contract."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for k, value in attrs:
            if k in ('href', 'src') and value:
                self.links.append(value)


def main():
    card = json.loads((ROOT / 'docs/run-card.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['submission_ready'] is False
    assert card['raster_sha256'] is None
    assert card['submission_name'] is None
    assert len(card['note']) <= 140
    assert card['experiments_run'] == card['weekly_slots_used'] == 0
    assert card['holdout']['dti'] is None and card['holdout']['ci95'] is None
    for file in (ROOT / 'docs').glob('*.html'):
        text = file.read_text()
        assert '<html lang="en">' in text
        parser = Links(); parser.feed(text)
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (file.parent / unquote(url.path)).resolve()
            assert target.is_relative_to(ROOT / 'docs'), f'Outside published site: {link}'
            assert target.exists(), f'Broken target in {file.name}: {link}'
            assert target.suffix.lower() not in ('.tif', '.tiff', '.zip'), 'No validated candidate is available'
    landing = (ROOT / 'index.html').read_text()
    assert 'url=docs/index.html' in landing
    assert 'NOT READY' in landing
    assert not list((ROOT / 'docs').rglob('*.tif'))
    print('PASS: local site links, no unvalidated TIFF download, negative status contract')


if __name__ == '__main__':
    main()
