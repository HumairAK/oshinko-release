import pytest
from config_sample import config
from ..app import create_app


@pytest.fixture(scope='module')
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config.update(config)
    c = app.test_client()
    yield c
