"""Create a public manifest without internal API URLs or raw archive paths."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = ("kind", "nct_id", "version", "retrieved_at_utc", "canonical_json_sha256", "source_url")


def reduce_manifest(source: Path, destination: Path) -> None:
    with source.open("r", encoding="utf-8-sig", newline="") as source_handle:
        rows = list(csv.DictReader(source_handle))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as destination_handle:
        writer = csv.DictWriter(destination_handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            nct_id = row["nct_id"]
            writer.writerow(
                {
                    "kind": row["kind"],
                    "nct_id": nct_id,
                    "version": row["version"],
                    "retrieved_at_utc": row["retrieved_at_utc"],
                    "canonical_json_sha256": row["canonical_json_sha256"],
                    "source_url": f"https://clinicaltrials.gov/study/{nct_id}?tab=history",
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    reduce_manifest(args.input, args.output)


if __name__ == "__main__":
    main()
