from typing import Dict
import cv2
import uuid
import os
import numpy as np
import datetime
from collections import deque
from shapely.geometry import Polygon

from utilities.util_functions import get_diff_contours, ts_to_strtime
from utilities.ffmpeg_video_writer import FFmpegVideoWriter
from utilities.shopper import Shopper
from utilities.interaction_event import InteractionEvent


class ShopperInteractionDetector:
    """
    Module Class for Detecting Shopper Interaction for single camera stream/video source. 
    
    `ShopperTracker` is used to track the shoppers in the stream. If confirm shopper is detected
    Video is recorded using `FFmpegVideoWriter` and after the shoppers are gone, 
    video recording is stopped and difference between the first and last frames is calculated 
    and differences are interpreted as polygons/contours, each contour indicates the interaction.
    An `InteractionEvent` object is retured.

    Attributes
    ----------
    aisle_region : dict
        Dictionary of polygons as aisle regions.
    config : dict
        Configuration parameters provided in yml file.
    fps : int or float
        FPS of video stream.
    frame_size : tuple(W,H,C)
        Frame size of the frames.
    camera_id : int or str
        camera_id of the video stream.
    shopper_tracker : ShopperTracker
        Shopper tracker to track the shoppers in the view.
    empty_frame_count : int
        Frames count with no detections .
    video_writer : FFmpegVideoWriter
        Video writer object for recording videos.
    real_time_interaction : bool
        Flag for enabling or disabling video recording.
    interaction_event : InteractionEvent
        Interaction event 
    frame_queue : deque[numpy.ndarray]
        frames queue for appending at the start of recorded videos.
    """
    
    def __init__(self, config, aisle_region, fps, frame_size, camera_id, crop_regions) -> None:
        """
        Constructs the ShopperInteraction module.

        Parameters
        ----------
        aisle_region : dict
            Dictionary of polygons as aisle regions.
        config : dict
            Configuration parameters provided in yml file.
        fps : int or float
            FPS of video stream.
        frame_size : tuple(W,H,C)
            Frame size of the frames.
        camera_id : int or str
            camera_id of the video stream.
        """

        self.crop_regions = crop_regions
        self.aisle_region = aisle_region
        self.config = config
        self.fps = fps
        self.frame_size = frame_size
        self.camera_id = camera_id
        
        Shopper.CONFIG_DURATION_THRES = self.config['shopper_interaction']['person_standing_time_wait']
        Shopper.CONFIG_IOU_THRES = self.config['shopper_interaction']['iou_thres']
        FFmpegVideoWriter.FFMPEG_BIN_PATH_WINDOWS = config['ffmpeg_path']

        self.shopper_tracker = ShoppersTracker(self.aisle_region)

        self.empty_frame_count = 0

        self.video_writer = None
        self.frame_queue = []

        # TODO:
        # self.is_meta_processing = False
        self.real_time_interaction = config['shopper_interaction']['real_time_interaction']
        
        self.interaction_event = None

        if self.real_time_interaction is True:
            queue_size = int(self.fps * self.config['shopper_interaction']['before_interaction_time'])
            self.frame_queue = deque([], maxlen=queue_size)


    def check_interacion(self, timestamp: float, img: np.ndarray, tracks):
        """
        Checks for the interaction.

        Parameters
        ----------
        timestamp : float
            Current timestamp of the frame.
        img : numpy.ndarray
            Current frame of the stream.
        tracks : dict
            Tracks of the current frame
        
        Returns
        -------
        None or InteractionEvent
        """
        
        # Updating the tracker state and checking current and confirmed shoppers
        current_shoppers, confirmed_shoppers_count = self.shopper_tracker.update(timestamp, tracks)

        # If confirmed shoppers are detected
        #TODO: Not sure if first condition is necessary 
        if len(current_shoppers) > 0 and confirmed_shoppers_count > 0:
            
            # Resetting the empty frame counter as shoppers are detected 
            self.empty_frame_count = 0

            # Start event recording if confirmed shopper is detected and recording is not already started
            if self.interaction_event is None:
                
                # Start time of the recording and event 
                start_time = ts_to_strtime(timestamp)

                # Initial frame of the event, Will be used to calculate interaction (starting and ending frames difference)
                start_frame = self.frame_queue[0].copy()

                video_path = None
                # If Video recording is enabled
                if self.real_time_interaction:
                    # Video will be recorded in temp folder
                    if not os.path.exists(self.config['tmp_folder']):
                        os.makedirs(self.config['tmp_folder'])
                    video_path = os.path.join(self.config['tmp_folder'], uuid.uuid4().hex+'.mp4')
                    # Initializing video writer
                    self.video_writer = FFmpegVideoWriter(video_path, fps=self.fps, frame_size=self.frame_size)
                    
                    # Writing previous frames stored in buffer
                    self.video_writer.write_queued_frames(self.frame_queue)
                    # clearing the frames buffer
                    self.frame_queue.clear()
                
                regions_dict = {'Aisle': self.aisle_region['r1']} | self.crop_regions[self.camera_id]
                # Constructing the Interaction event with initial data available
                self.interaction_event = InteractionEvent(self.camera_id, start_time, start_frame, video_path, regions_dict)

        # wait for empty aisle (when  no shopper  is in front of aisle)
        # TODO: time calculation can be done using timestamps
        elif int(self.empty_frame_count/self.fps) < self.config['shopper_interaction']['wait_threshold']:
            self.empty_frame_count = self.empty_frame_count + 1
        
        # if no detections are found and aisle is empty (or wait_threshold is reached)
        else:

            # Check if interaction event was initiated
            if self.interaction_event is not None:
                # Closing the writer id video recording was started
                if self.video_writer is not None:
                    self.video_writer.close_writer()
                    self.video_writer = None

                # end time of the interaction event
                end_time = ts_to_strtime(timestamp)
                
                # Calculating interaction contours (based on the differences between starting and ending frame)
                interaction_contours = get_diff_contours(self.interaction_event.start_frame, img.copy(), self.aisle_region, self.config['shopper_interaction']['area_percentage'][self.camera_id] )
                
                # updating the interaction event
                self.interaction_event.set_interaction(end_time, img, interaction_contours)
                # setting the stats during the event
                self.interaction_event.set_stats(   self.shopper_tracker.get_confirmed_shoppers(), 
                                                    len(self.shopper_tracker.shoppers), 
                                                    self.shopper_tracker.count)
                # Clearing the shopper tracker state/memory for next event
                self.shopper_tracker.clear()

        
        if self.real_time_interaction:
            self.frame_queue.append(img)
            if self.video_writer is not None:
                self.video_writer.write(img)

        # Checking if event completed to return the event
        if self.video_writer is None and self.interaction_event is not None:
            event = self.interaction_event
            self.interaction_event = None
            return event
        # Returing none otherwise
        return None


class ShoppersTracker:
    """
    Class to for Shopper Tracker.

    Attributes
    ----------
    aisle_region : dict
        Dictionary of polygons as aisle regions
    shoppers : list[Shopper]
        List of tracked shoppers.
    """

    def __init__(self, aisle_region) -> None:
        """
        Constructs the tracker object.

        Parameters
        ----------
        aisle_region : dict
            Dictionary of polygons as aisle regions

        """
        self.aisle_region = aisle_region
        self.count = 0
        self.shoppers = {}
    
    def _calculate_shoppers_IOU(self, aisle_regions, tracks):
        """
        Calculates IOU, Not exactly IOU but rather IoBB. Calculates bbox overlap over ROI (polygon)   

        Parameters
        ----------
        aisle_regions : dict
            Dictionary of polygons as aisle regions.
        tracks : numpy.ndarray
            Tracks from box tracker.

        Returns
        -------
        list[dict[float]]
        list of floats for each shoppers iou
        """

        iou_list = [{} for _ in range(0, len(aisle_regions.values()))]
        aisle_regions_list = list(aisle_regions.values())

        for i in range(0, len(aisle_regions_list)):
            region_poly = Polygon(aisle_regions_list[i])
            for x1,y1,x2,y2,id in tracks:
                xyxy2poly = Polygon([ [x1, y1], 
                                        [x1, y2], 
                                        [x2, y2], 
                                        [x2, y1], 
                                        [x1, y1]])
                intersection = xyxy2poly.intersection(region_poly).area
                iou_list[i][id] = intersection / xyxy2poly.area

        return iou_list

    def _update_shoppers(self, timestamp, iou_list):
        """
        Updates existing shoppers state and registers new one.

        Attributes
        ----------
        timestamp : float
            Current timestamp.
        iou_list : list[dict[float]]
            List of each shoppers IOU in each region.
        
        Returns
        -------
        Tuple[list[shoppers], int]
        """

        current_shoppers = {}
        confirmed_count = 0
        # For each aisle region
        for shoppers_iou in iou_list:
            # for each region in camera view
            for id, iou in shoppers_iou.items():
                shopper = self.shoppers.get(id, None)
                if shopper is None:
                    shopper = Shopper(id, timestamp)
                    self.count += 1
                else:
                    shopper.update_status(timestamp, iou)
                    if shopper.status == Shopper.STATUS_CONFIRMED:
                        confirmed_count += 1

                self.shoppers[id] = shopper
                current_shoppers[id] = shopper
        return current_shoppers, confirmed_count

    def get_confirmed_shoppers(self):
        """
        Returns confirmed shoppers.

        Returns
        -------
        dict of shoppers
        """
        
        return {id: shopper
                    for id, shopper in self.shoppers.items() 
                        if shopper.status == Shopper.STATUS_CONFIRMED}
    
    def clear(self):
        """
        Clears the state of tracker

        Returns
        -------
        None
        """

        self.shoppers.clear()

    def update(self, timestamp, tracks):
        """
        Updates the state of tracker.

        
        """
        
        if len(tracks) > 0:
            
            iou_list = self._calculate_shoppers_IOU(self.aisle_region, tracks)
            current_shoppers, confirmed_count = self._update_shoppers(timestamp, iou_list)
            return current_shoppers, confirmed_count
        return {}, 0

