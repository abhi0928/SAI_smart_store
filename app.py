from stream_handlers.stream_handler import InputStreamHandler
import os
from glob import glob
import pyyaml

config = yaml.safe_load(open('stream_handlers/config.yml', 'r'))

stream_handler = InputStreamHandler(config['input_stream'])

for frame_id, timestamps, imgs in stream_handler:
    # operations for customer activity on different camera frames
    pass
