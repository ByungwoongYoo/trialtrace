"""Fail when measured Python branch coverage is below the required threshold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    """Read Coverage.py JSON output and enforce branch coverage directly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", type=Path, default=Path("coverage.json"))
    parser.add_argument("--minimum", type=float, default=80.0)
    args = parser.parse_args()

    totals = json.loads(args.report.read_text(encoding="utf-8"))["totals"]
    total = int(totals["num_branches"])
    covered = int(totals["covered_branches"])
    percentage = 100.0 if total == 0 else covered / total * 100
    if percentage < args.minimum:
        message = f"Branch coverage {percentage:.2f}% ({covered}/{total}) is below {args.minimum:.2f}%."
        raise SystemExit(message)
    print(f"Branch coverage {percentage:.2f}% ({covered}/{total}) meets the {args.minimum:.2f}% requirement.")


if __name__ == "__main__":
    main()
