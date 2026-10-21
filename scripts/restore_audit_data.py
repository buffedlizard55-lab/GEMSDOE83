"""Recover only the three small hash-pinned audit inputs, never predictions.

Uses the upstream data manifest unchanged. This is not a shared feature builder,
submission writer, or holdout evaluator. Requires authenticated gh CLI.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    entries = json.loads((ROOT / 'evidence/upstream/registry__data_manifest.json').read_text())['files']
    receipt = []
    for entry in entries:
        if entry['id'] not in {'labels', 'existing_faults', 'sample_submission'}:
            continue
        dest = ROOT / 'data' / entry['dest']
        dest.parent.mkdir(parents=True, exist_ok=True)
        expected = entry['sha256']
        if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest() != expected:
            temp = dest.with_suffix('.partial')
            try:
                with temp.open('wb') as out:
                    subprocess.run(['gh', 'api', f"repos/{entry['repo']}/contents/{entry['path']}?ref={entry['ref']}",
                                    '-H', 'Accept: application/vnd.github.raw+json'], stdout=out, check=True)
                if hashlib.sha256(temp.read_bytes()).hexdigest() != expected:
                    raise ValueError(f"Hash mismatch: {entry['id']}")
                temp.replace(dest)
            finally:
                temp.unlink(missing_ok=True)
        receipt.append({'id': entry['id'], 'sha256': expected, 'bytes': dest.stat().st_size,
                        'provenance': entry['provenance']})
    assert len(receipt) == 3, 'Incomplete audit manifest'
    (ROOT / 'evidence/data_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Verified three mirrored audit inputs. NOT organizer-authenticated. NOT submissions.')


if __name__ == '__main__':
    main()
