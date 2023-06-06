#from __future__ import annotations
from typing import Tuple

import logging
import numpy as np

from threading import Thread
from stream_handlers.input_stream import InputStream


#TODO: Config & params validation
class InputStreamHandler:
    """
    Class to open and handle multiple camera sources.

    Attributes
    ----------
    mode : str , 'stream' or 'file'
        Input source mode for all streams.
    frame_size : tuple
        Frame size to resize source frames for all streams.
    queue_size : int
        Buffer size to hold extracted frames for each stream.
    retry_limit : int
        Max number Retries to attempt to open the camera/stream/source if it fails for each stream.
        Ignored if mode is 'file'
    parsed_sources : list[dict]
        List of parsed input sources.
    streams : list[InputStream]
        List of all open streams
    camera_to_idx : dict
        Mapping of camera id to its index in list
    """
    
    def __init__(self, sources, frame_size = (1920, 1080), mode = "file", queue_size = 150, retry_limit = 30):
        """
        Constructs the StreamHandler object.

        Parameters
        ----------
        sources : str or list[dict]
            Input video sources. can either be a csv as .txt file path or a list of dict consisiting of 
            keys 'camera_id' and 'source'
        mode : str , 'stream' or 'file'
            Input source mode for all streams.
        frame_size : tuple
            Frame size to resize source frames for all streams.
        queue_size : int
            Buffer size to hold extracted frames for each stream.
        retry_limit : int
            Max number Retries to attempt to open the camera/stream/source if it fails for each stream.
            Ignored if mode is 'file'
        """
        
        self.mode = mode
        self.queue_size = queue_size
        self.retry_limit = retry_limit
        self.frame_size = frame_size
        self.streams = []
        self.camera_to_idx = {}
        

        if isinstance(sources, str) and sources.endswith("txt"):
            self.parsed_sources = self._parse_stream_input(sources)
        elif isinstance(sources, list):
            self.parsed_sources = sources
        else:
            raise ValueError("Invalid `sources` format, can either be path to txt file or array of dicts and cannot be empty")

        if len(self.parsed_sources) < 1:
            raise Exception("No stream source found")


    def _parse_stream_input(self, src):
        """
        Read the sources and camera_ids from input file

        Parameters
        ----------
        src: str
            path of source file containing stream sources and camera_ids

        Returns
        --------
        list[dict]
        source(list of sources), types(list of camera_ids)
        """
        sources=[]
        with open(src, 'r') as f:
            for x in f.read().strip().splitlines():
                source,camera_id=x.split(",")
                sources.append({'source': source, 'camera_id': camera_id})
                
        return sources


    def start(self):
        """
        Opens the video sources and creates threads for each camera

        Returns
        ------
        list[InputStream]
        List of all open streams
        """
        
        n = len(self.parsed_sources)
        for i, src in enumerate(self.parsed_sources):  # index, source
            # Start thread to read frames from video stream
            logging.info(f'{i + 1}/{n}: {src}... ')
            
            # Preparing kwargs for initializing the InputStream object
            src['queue_size'] = self.queue_size
            src['retry_limit'] = self.retry_limit
            src['mode'] = self.mode
            src['frame_size'] = self.frame_size
            stream = InputStream(**src)

            # opening video handles of the stream
            stream.start_stream()
            # delegating the stream to a new thread
            thread = Thread(target=stream.update, daemon=True)
            thread.start()
            
            self.camera_to_idx[stream.camera_id] = i
            self.streams.append(stream)

        return self.streams


    def __iter__(self):
        self.frame_id = -1
        return self

    def __next__(self):
        """
        Iterates over all stream buffers and returns a batch of frames with timestamps
        """

        self.frame_id += 1
        frames = []
        timestamps = []

        # Iterating all streams
        for x in range(len(self.streams)):
            # Checking if the stream buffer is not empty
            if len(self.streams[x].buffer) == 0:
                logging.debug(f"{self.streams[x].source} Frame buffer is empty...")
                frames.append(None)
                timestamps.append(0.0)
            else:
                timestamp, frame = self.streams[x].buffer.popleft()
                frames.append(frame)
                timestamps.append(timestamp)


        # Breaking the loop if all of the stream threads stop
        if not any([stream.running or len(stream.buffer)>0 for stream in self.streams]):
            raise StopIteration
        return self.frame_id, timestamps, frames

