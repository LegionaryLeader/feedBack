import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'plugins' / 'tuner'))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import routes as tuner_routes


@pytest.fixture
def config_dir(tmp_path):
    return tmp_path


@pytest.fixture
def client(config_dir):
    app = FastAPI()
    tuner_routes.setup(app, {
        "config_dir": str(config_dir),
        "register_tuning_provider": lambda pid, fn: None,
        "unregister_tuning_provider": lambda pid: None,
    })
    return TestClient(app)
