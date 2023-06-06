import time
import logging
import cv2

from collections import deque

class InputStream:
    """
    Class to open video source and extract frames into a buffer.

    Attributes
    ----------
    buffer : collections.deque
        Buffer to store extracted frames.
    fps : int or float
        FPS of the video source.
    cap : cv2.VideoCapture
        Handle of opened video source.
    running : bool
        Flag to tell if video source is still open.
    frame_id : int
        Current frame id i.e. counter
    camera_id : int
        Unique camera id to identify a specific camera. 
    source : str
        An rtsp address or path to a video file, basically anything that cv2.VideoCapture accepts.
    mode : str , 'stream' or 'file'
        Input source mode.
    frame_size : tuple
        Frame size to resize source frames.
    queue_size : int
        Buffer size to hold extracted frames.
    retry_limit : int
        Max number Retries to attempt to open the camera/stream/source if it fails.
        Ignored if mode is 'file'
    """
    
    def __init__(self,camera_id, source, mode, frame_size, queue_size = 150, retry_limit = 30):
        """
        Constructs the InputStream object.

        Parameters
        ----------
        camera_id : int
            Unique camera id to identify a specific camera. 
        source : str
            An rtsp address or path to a video file, basically anything that cv2.VideoCapture accepts.
        mode : str , 'stream' or 'file'
            Input source mode.
        frame_size : tuple
            Frame size to resize source frames.
        queue_size : int
            Buffer size to hold extracted frames.
        retry_limit : int
            Max number Retries to attempt to open the camera/stream/source if it fails.
            Ignored if mode is 'file'
        """
        
        self.buffer = deque(maxlen=int(round(queue_size)))
        self.source = source
        self.camera_id = camera_id
        self.queue_size = queue_size
        self.retry_limit = retry_limit
        self.mode = mode
        self.frame_size = tuple(frame_size)

        #TODO: Check and remove unused properties
        self.frame = None
        self.input_frame_size = None
        self.fps = None
        self.cap = None

        self.running = True

        self.frame_id = 0

    
    def _get_timestamp(self, current_frame: int) -> float:
        """
        Returns the current timestamp of the input. 
        If input mode is 'file', it calculates the duration of video using current frame number and fps.
        otherwise it returns the system timestamp.

        Parameters
        ----------
        current_frame : int
            Sequence number of the current frame
        
        Returns
        -------
        float
        """

        if self.mode == 'file':
            seconds = current_frame / self.fps
            return seconds

        return time.time()

    def start_stream(self):
        """
        Initializes VideoCapture object for the stream.

        Returns
        -------
        None
        """
        
        self.cap = cv2.VideoCapture(self.source)
        # TODO: assertions vs throwing exceptions
        assert self.cap.isOpened(), f'Failed to open {self.source}'
        # w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        _, self.frame = self.cap.read()
        H, W, C = self.frame.shape
        self.input_frame_size = (W, H, C)
    
    def __repr__(self):
        return repr(f'Stream(source: {self.source} camera_id: {self.camera_id} fps: {self.fps})')

    def update(self):
        """
        Reads next stream frame in a daemon thread and places it in the buffer.

        Returns
        -------
        None
        """

        retry_count = 0
        while self.cap.isOpened():
            # Check if buffer is full
            if len(self.buffer) == self.queue_size:
                logging.debug("Frame buffer is full. (150 frames)")
                continue
            
            # Read frame from camera
            success, frame = self.cap.read()
            if success and frame is not None:
                logging.debug("Adding Frame to buffer...")
                frame = cv2.resize(frame, self.frame_size[:2])
                self.frame_id += 1
                timestamp = self._get_timestamp(self.frame_id)
                self.buffer.append( (timestamp, frame) )
            else:
                logging.debug(f"Could not read next frame from stream. ({self.source})")
                retry_count += 1
                if retry_count > self.retry_limit and self.mode == 'stream':
                    logging.debug(f"Retry limit reached ({self.retry_limit}). Attempting to reopen camera ({self.source})")
                    retry_count = 0
                    # Close and reopen camera with some wait
                    self.cap.release()
                    time.sleep(1)
                    self.cap = cv2.VideoCapture(self.source)
                elif self.mode == 'file':
                    break
        self.running = False
        logging.debug("Exiting...")
