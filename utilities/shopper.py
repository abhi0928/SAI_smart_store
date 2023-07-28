
class Shopper:
    """
    Class to store the Shopper data.

    Attributes
    ----------
    id : int
        Track id of the shopper.
    start_timestamp : float
        Timestamp when the shopper was first detected.
    interaction_duration : int 
        Standing/Interaction Duration in seconds.
    status : int [Shopper.STATUS_xx]
        Status of the shopper. See project docs for detail.

    Basic Usage
    -----------
    Constructing the shopper object

    >>> Shopper.CONFIG_DURATION_THRES = 3 # seconds
    >>> Shopper.CONFIG_IOU_THRES = 0.5
    >>> s = Shopper(...)

    Updating the shopper status

    >>> s.update_status(...)
    """
    
    STATUS_DETECTED = 0     # Detected in frame / Default status
    STATUS_SHOPPER = 1      # Found inside aisle region
    STATUS_CONFIRMED = 2    # Stayed long enough (specified in config) in aisle region

    # IOU threshold of shopper with asile region 
    CONFIG_IOU_THRES = None
    # Duration in seconds thresold to confirm the shopper
    CONFIG_DURATION_THRES = None

    def __init__(self, id, start_timestamp):
        """
        Constructs the shopper object
        
        Parameters
        ----------
        id : int
            Track id of the shopper.
        start_timestamp : float
            timestamp when the shopper was first detected.
        fps : int
            FPS of the stream in which shopper is detected.
        """

        if Shopper.CONFIG_DURATION_THRES is None or Shopper.CONFIG_IOU_THRES is None:
            raise Exception("CONFIG of shopper is not set. Follow docs to set \
                                the config params before constructing the object")

        self.id  = id
        self.start_timestamp = start_timestamp
        self.interaction_duration = 0
        self.status = Shopper.STATUS_DETECTED

    def update_status(self, timestamp, iou):
        """
        Updates the shopper status based on IOU and current frame number

        Parameters
        ----------
        current_frame_no : int
            Current Frame number of the stream.
        iou : decimal
            IOU of the shopper with aisle region.

        Returns
        -------
        None
        """
        
        if iou >= Shopper.CONFIG_IOU_THRES and self.status != Shopper.STATUS_CONFIRMED:
            self.status = Shopper.STATUS_SHOPPER

        self.interaction_duration = timestamp - self.start_timestamp
        if self.interaction_duration > Shopper.CONFIG_DURATION_THRES:
            self.status = Shopper.STATUS_CONFIRMED