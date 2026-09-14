"""Verify that an installed TrialTrace wheel contains a usable corpus."""

from __future__ import annotations

import tempfile
from pathlib import Path

from trialtrace import __version__
from trialtrace.db import DATA_DIR, EXPECTED_COUNTS, build_database


def main() -> None:
    """Build a database using only resources supplied by the installed package."""
    if not DATA_DIR.is_dir():
        message = f"Installed corpus directory is missing: {DATA_DIR}"
        raise RuntimeError(message)
    with tempfile.TemporaryDirectory(prefix="trialtrace-wheel-") as temp_dir:
        database_path = Path(temp_dir) / "trialtrace.db"
        counts = build_database(database_path)
        if counts["trials"] != EXPECTED_COUNTS["trials"]:
            message = f"Installed corpus check failed: {counts}"
            raise RuntimeError(message)
    print(f"TrialTrace {__version__} installed-wheel smoke test passed")


if __name__ == "__main__":
    main()
