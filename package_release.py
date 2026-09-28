"""Build deterministic versioned and compatibility resource-pack archives."""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parent
PACK = ROOT / "resourcepacks" / "Citizons_Railway"
DIST = ROOT / "dist"
VERSION_FILE = PACK / "VERSION"
PACK_META = PACK / "pack.mcmeta"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def main() -> None:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not version or any(character.isspace() for character in version):
        raise ValueError("VERSION must contain one non-empty token")

    metadata = json.loads(PACK_META.read_text(encoding="utf-8"))
    if metadata.get("pack", {}).get("pack_format") != 15:
        raise ValueError("pack.mcmeta pack_format must remain 15")
    metadata["pack"]["description"] = (
        f"Citizons Railway {version} · MTR 4.0.3 / Minecraft 1.20.1"
    )
    PACK_META.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    archive_path = DIST / f"Citizons_Railway-{version}.zip"
    compatibility_path = DIST / "Citizons_Railway.zip"
    DIST.mkdir(exist_ok=True)
    with ZipFile(archive_path, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(path for path in PACK.rglob("*") if path.is_file()):
            entry = ZipInfo(source.relative_to(PACK).as_posix(), FIXED_TIME)
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, source.read_bytes(), compresslevel=9)
    compatibility_path.write_bytes(archive_path.read_bytes())
    print(f"Built {archive_path.relative_to(ROOT)} and {compatibility_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
