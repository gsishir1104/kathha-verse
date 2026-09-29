import os
from pathlib import Path
import tempfile
os.environ["DEMO_MODE"] = "true"
os.environ["MAIL_ENABLED"] = "false" # Tests never send real email.

# Select an isolated database before any test module imports application models.
_test_dir = tempfile.TemporaryDirectory(prefix='storylens-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(_test_dir.name) / 'test.db').as_posix()

import pytest

@pytest.fixture(autouse=True)
def require_isolated_database():
    from app.db import engine
    assert Path(engine.url.database).resolve().parent == Path(_test_dir.name).resolve(), 'Refusing tests against a non-test database'


def pytest_sessionfinish(session, exitstatus):
    from app.db import engine
    engine.dispose()
    _test_dir.cleanup()
