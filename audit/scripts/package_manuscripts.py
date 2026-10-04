"""Package the conference and journal manuscripts into submission ZIPs (Phase 3).

Each ZIP contains the .tex source, the compiled .pdf, the figures/ and tables/
directories, references and the README. Build artifacts (aux/log/out) are
excluded. A manifest with SHA-256 hashes is written alongside each ZIP.
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAN = ROOT / "final_manuscripts"

SPECS = {
    "conference": MAN / "conference",
    "journal": MAN / "journal",
}
EXCLUDE_SUFFIX = {".aux", ".log", ".out", ".blg", ".bbl", ".synctex.gz"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def package(name: str, base: Path) -> dict:
    zip_path = MAN / f"{name}_manuscript.zip"
    members = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(base.rglob("*")):
            if p.is_dir():
                continue
            if p.suffix in EXCLUDE_SUFFIX or p.name.endswith(".synctex.gz"):
                continue
            arc = Path(name) / p.relative_to(base)
            z.write(p, arc.as_posix())
            members.append({"arcname": arc.as_posix(), "sha256": sha256(p),
                            "bytes": p.stat().st_size})
    manifest = MAN / f"{name}_manuscript_manifest.json"
    import json
    manifest.write_text(json.dumps(
        {"zip": zip_path.name, "files": len(members), "members": members}, indent=2))
    return {"zip": str(zip_path.relative_to(ROOT)),
            "bytes": zip_path.stat().st_size, "files": len(members)}


def main():
    out = {}
    for name, base in SPECS.items():
        out[name] = package(name, base)
        print(f"{name}: {out[name]}")
    return out


if __name__ == "__main__":
    main()
