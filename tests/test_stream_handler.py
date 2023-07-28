import imp
import pytest
import cv2
from stream_handlers.stream_handler import InputStreamHandler


@pytest.fixture()
def stream_handler(config):
    assert 'input_streams' in config
    assert 'sources' in config['input_streams']
    stream_handler = InputStreamHandler(**config['input_streams'])
    return stream_handler

def test_input_stream_handler(stream_handler):
    pass

def test_input_stream_handler_file():
    stream_handler = InputStreamHandler('tests/streams.txt')

def test_input_stream_handler_valueerror():
    with pytest.raises(ValueError) as e:
        stream_handler = InputStreamHandler('tests/streams')

def test_input_stream_handler_exception():
    with pytest.raises(Exception) as e:
        stream_handler = InputStreamHandler([])

# Takes long time decrease video files with less frames
def test_input_stream_handler_start(stream_handler):
    stream_handler.start()
    counter = [0,0]
    for idx, imgs in enumerate(stream_handler):
        counter[0] += 1 if imgs[0] is not None else 0
        counter[1] += 1 if imgs[1] is not None else 0
    print(stream_handler.camera_to_idx)