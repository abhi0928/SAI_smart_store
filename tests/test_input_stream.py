import pytest

from stream_handlers.input_stream import InputStream


@pytest.fixture()
def stream(config):
    assert 'input_streams' in config
    assert len(config['input_streams']) > 0
    stream = InputStream(**config['input_streams'][0])
    return stream

def test_input_stream(stream):
    pass