import subprocess as sp
import numpy as np

class FFmpegVideoWriter:
    """
    FFmpeg based video writer class. Uses subprocess to open FFpmeg writer and writes to it using pipe.

    Attributes
    ----------
    path : str
        Full path of video file to be written.
    frame_size : tuple, list or any indexable 
        Frame size as W,H (with first element as width and second as height) of the video aka resolution.
    fps : int
        FPS of the video.
    pipe : subprocess.Popen
        Popen object to write frames to ffmpeg writer

    Basic Usage
    -----------
    Construct a VideoWriter
    
    >>> FFmpegVideoWriter.FFMPEG_BIN_PATH_WINDOWS = '/path/to/ffmpeg binary'
    >>> writer = FFmpegVideoWriter('/path/video.mp4', 30, (1920,1080))

    Write frames using the writer

    >>> writer.write(frame)

    Close the writer

    >>> writer.close_writer()
    """
    
    # FFmpeg binary/executable path
    FFMPEG_BIN_PATH_WINDOWS = None

    def __init__(self, path, fps, frame_size):
        """
        Constructs the FFmpegVideoWriter. 
        Set the `FFmpegVideoWriter.FFMPEG_BIN_PATH_WINDOWS` before using.

        Parameters
        ----------
        path : str
            Full path of video file to be written.
        frame_size : tuple, list or any indexable 
            Frame size as W,H (with first element as width and second as height) of the video aka resolution.
        fps : int
            FPS of the video.
        """
        
        if FFmpegVideoWriter.FFMPEG_BIN_PATH_WINDOWS is None:
            raise Exception("FFMPEG executable path is not set. Set it using \
                                `FFmpegVideoWriter.FFMPEG_BIN_PATH_WINDOWS = '/path/to/ffmpeg'` before constructing the object")

        self.path = path
        self.frame_size = frame_size
        self.fps = fps
        self.pipe = None

        self._get_ffmpeg_pipe()

    def write_queued_frames(self, queue):
        """
        Writes list or queue of frames (np.ndarray).

        Parameters
        ---------
        queue : list or any iterable of np.ndarrays
            List of frames to write.
        """
        
        for frame in queue:
            self.write(frame)

    def write(self, frame):
        """
        Writes a single frame.

        Parameters
        ----------
        frame : numpy.ndarray
            Frame to write to the video.
        """
        
        self.pipe.stdin.write(frame.astype(np.uint8).tobytes())

    def close_writer(self):
        """
        Closes the video writer and sets the pipe to None
        """

        if self.pipe is not None:
            self.pipe.stdin.close()
            self.pipe = None

    def _get_ffmpeg_pipe(self):
        """
        Creates a subprocess using subprocess.Popen to write video. 
        """
        
        command = [FFmpegVideoWriter.FFMPEG_BIN_PATH_WINDOWS,
                   '-y',  # (optional) overwrite output file if it exists
                   '-f', 'rawvideo',
                   '-vcodec', 'rawvideo',
                   '-s', f"{self.frame_size[0]}x{self.frame_size[1]}",  # size of one frame
                   '-pix_fmt', 'bgr24',
                   '-r', str(self.fps),  # frames per second
                   '-i', '-',  # The imput comes from a pipe
                   '-an',  # Tells FFMPEG not to expect any audio
                   '-c:v', 'libx264',
                   '-pix_fmt', 'yuv420p',
                   '-preset', 'ultrafast',
                   '-f', 'flv',
                   '-crf', '30',
                   '-loglevel','quiet',
                   self.path]
        pipe = sp.Popen(command, stdin=sp.PIPE)
        self.pipe = pipe
