from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BLOCKED_MARKERS = ("agpl", "gpl", "unknown", "proprietary", "commercial")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail on unresolved or strong-copyleft release dependencies.")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    rows = json.loads(args.report.read_text(encoding="utf-8"))
    errors: list[str] = []
    for row in rows:
        name = str(row.get("Name", row.get("name", "unknown")))
        license_value = str(row.get("License", row.get("license", "UNKNOWN"))).lower()
        if any(marker in license_value for marker in BLOCKED_MARKERS):
            errors.append(f"{name}: requires license review ({license_value})")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"dependency license check: ok ({len(rows)} packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
