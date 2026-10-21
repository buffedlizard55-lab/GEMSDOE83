#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/data/raw}"
MANIFEST="$ROOT/registry/data_manifest.json"
mkdir -p "$DEST" "$ROOT/data/external" "$ROOT/data/processed"
python3 - "$MANIFEST" "$DEST" <<'PY'
import json, subprocess, sys, hashlib, os
from pathlib import Path
manifest, dest = Path(sys.argv[1]), Path(sys.argv[2])
spec = json.loads(manifest.read_text())
fail=[]
def gh(repo, ref, path, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as fh:
        subprocess.run(["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "-H", "Accept: application/vnd.github.raw"], stdout=fh, check=True)
for f in spec["files"]:
    target = dest / f["dest"]
    if "parts" in f:
        chunks=[]
        for i,p in enumerate(f["parts"]):
            c=dest / f"_part-{i:03d}"
            gh(f["repo"], f["ref"], p, c)
            chunks.append(c)
        with target.open("wb") as out:
            for c in chunks:
                out.write(c.read_bytes())
        for c in chunks: c.unlink()
    else:
        gh(f["repo"], f["ref"], f["path"], target)
    got=hashlib.sha256(target.read_bytes()).hexdigest()
    nbytes=os.path.getsize(target)
    ok=(got==f["sha256"]) and (nbytes==f["bytes"])
    print(("PASS " if ok else "FAIL ") + f"{f['id']:24s} {nbytes:>12,} bytes  {got[:16]}...")
    if not ok: fail.append(f["id"])
print(json.dumps({"verified": len(spec["files"])-len(fail), "failed": fail}, indent=1))
sys.exit(1 if fail else 0)
PY
