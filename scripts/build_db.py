"""Build the TrialTrace SQLite database from the frozen CSV corpus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from trialtrace.db import DATA_DIR, DEFAULT_DB_PATH, build_database  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument(
        "--skip-hash-check",
        action="store_true",
        help="Development only: validate schema and counts without enforcing the frozen SHA-256 values.",
    )
    args = parser.parse_args()
    result = build_database(args.output, args.data_dir, verify_hashes=not args.skip_hash_check)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
