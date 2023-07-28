import yaml
import pytest


@pytest.fixture()
def config():
    with open("config.yml") as f:
        config = yaml.safe_load(f)
    
    assert 'detector' in config
    return config
