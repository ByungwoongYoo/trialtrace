from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from trialtrace.app import create_app
from trialtrace.db import DATA_DIR, build_database


@pytest.fixture(scope="session")
def database_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("database") / "trialtrace.db"
    build_database(path, DATA_DIR)
    return path


@pytest.fixture(scope="session")
def client(database_path: Path):
    app = create_app(database_path)
    with TestClient(app) as test_client:
        yield test_client
