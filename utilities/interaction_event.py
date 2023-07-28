import os
import shutil
import cv2
from threading import Thread


from utilities.polygon_manager import draw_regions, draw_polygon
from utilities.util_functions import create_interaction_montage, bbox_in_aisle_region_key

class InteractionEvent:
    """
    Class to store the Interaction event data.

    Attributes
    ----------
    camera_id : str or int
        Camera id of the interaction event.
    start_time : str
        Start time of the interaction event. Time in %H:%M:%S format.
    start_frame : numpy.ndarray
        Initial frame at the start of interaction event.
    video_path : str
        Path of the interaction event video.
    end_time : str
        Ending time of the interaction event. Time in %H:%M:%S format.
    end_frame : numpy.ndarray
        Last empty frame of interaction event.
    interactions_count : int
        Total interactions detected.
    interaction_contours : list of contours
        Contours of the interactions
    total_detected : int
        Total detected persons during the event.
    total_confirmed : int
        Total confirmed shoppers during the event.
    overall_total : int
        Total detections of all previous events.
    count_dict : dict
        Stats for shopper interaction duration for the Inference_Database.
    interaction_frame : numpy.ndarray
        Visualization of the interaction

    Basic Usage
    -----------
    Cosntruct an event object when event starts

    >>> e = InteractionEvent(...)

    Update the event object when event completes

    >>> e.set_interaction(...)
    >>> e.set_stats(...)

    Save and move event files

    >>> e.save_files(...)
    """
    
    def __init__(self, camera_id, start_time, start_frame, video_path, regions_dict) -> None:
        """
        Constructs the InteractionEvent

        Parameters
        ----------
        camera_id : str or int
            Camera id of the interaction event.
        start_time : str
            Start time of the interaction event. Time in %H:%M:%S format.
        start_frame : numpy.ndarray
            Initial frame at the start of interaction event.
        video_path : str
            Path of the interaction event video.
        """

        self.regions_dict = regions_dict
        self.camera_id = camera_id
        self.start_time = start_time
        self.start_frame = start_frame
        self.video_path = video_path

        self.interactions_count = 0
        self.interaction_contours = None
        self.end_frame = None
        self.end_time = None
        self.region = []
        
    def set_interaction(self, end_time, end_frame, interaction_contours):
        """
        Sets the interaction data after event is complete.

        Parameters
        ----------
        end_time : str
            Ending time of the interaction event. Time in %H:%M:%S format.
        end_frame : numpy.ndarray
            Last empty frame of interaction event.
        interaction_contours : list of contours
            Contours of the interactions

        Returns
        -------
        None
        """

        self.end_time = end_time
        self.end_frame = end_frame
        self.interactions_count = len(interaction_contours) 
        self.interaction_contours = interaction_contours
    
    def set_stats(self, confirmed_shoppers, total_detected, accumulative_total):
        """
        Sets the event statistics

        Parameters
        ----------
        confirmed_shoppers : list of Shoppers
            Confirmed shoppers during the event.
        total_detected : int
            Total detected persons during the event.
        accumulative_total : int
            Total detections of all previous events accumulated. 

        Returns
        -------
        None
        """

        self.total_detected = total_detected
        self.total_confirmed = len(confirmed_shoppers)
        self.overall_total = accumulative_total
        
        #Possible TODO: Move these calculations to Inference_Database class

        # Calculating stats of duraition spent on camera
        self.count_dict = {
                'mt_60': 0, # more then 60 seconds
                'mt_50': 0, # between 50  and 60 seconds
                'mt_40': 0, # between 40  and 50 seconds
                'mt_30': 0, # between 30  and 40 seconds
                'mt_20': 0, # between 20  and 30 seconds
                'mt_10': 0, # between 10  and 20 seconds
            }

        durations = [confirmed_shoppers[shp].interaction_duration for shp in confirmed_shoppers]

        for i in durations:
            if i <= 10:
                self.count_dict['mt_10'] += 1
            elif i <= 20:
                self.count_dict['mt_20'] += 1
            elif i <= 30:
                self.count_dict['mt_30'] += 1
            elif i <= 40:
                self.count_dict['mt_40'] += 1
            elif i <= 50:
                self.count_dict['mt_50'] += 1
            else:
                self.count_dict['mt_60'] += 1

    def __repr__(self):
        """Representaion of the shopper object"""
        
        return "Shopper"+str((self.camera_id,
                self.start_time,
                self.start_frame,
                self.end_time,
                self.end_frame,
                self.video_path,
                self.interactions_count,
                self.total_detected,
                self.count_dict))
    
    def __str__(self):
        return self.__repr__()

    def determin_crop_region(self, crop_regions):
            
        for c in self.interaction_contours:
            xywh = cv2.boundingRect(c)
            r = bbox_in_aisle_region_key(xywh, crop_regions)
            if r is not None:
                self.region.append(r)


    def save_files(self, base_dir):
        """
        Saving and moving interaction event files to their respective directory given by `base_dir`.
        Creates the direcotry if does not exist

        Parameters
        ----------
        base_dir : str
            Path of the events directory

        Returns
        -------
        None
        """
        
        # if any interaction was detected
        if self.interactions_count > 0:

            # Path for the specifc camera events
            destination_path = os.path.join(base_dir, str(self.camera_id))
            if not os.path.exists(destination_path):
                os.makedirs(destination_path)

            # Checking if the Video evidence was created/recorded
            if self.video_path is not None:
                new_video_path = os.path.join(destination_path, f'{self.start_time.replace(":","_")}.mp4')
                # moving the video from temp directory to specific camera event directory
                shutil.move(self.video_path, new_video_path)
            
            # Visualization of the interaction i.e. highlighting interaction areas
            start_frame = draw_regions(self.start_frame, self.camera_id, self.regions_dict)
            self.interaction_frame = create_interaction_montage(self.start_frame, self.end_frame, self.interaction_contours)

            # Saving the interaction image
            self.image_path = os.path.join(destination_path,f'{self.start_time.replace(":","_")}_interaction.jpg')
            image_writing_thread = Thread(target=cv2.imwrite, args=(self.image_path, self.interaction_frame), daemon=True)
            image_writing_thread.start()

        else:
            # if no interaction is detected, move the video from temp dir to Ambigious directory
            #TODO: make the `Ambigious` configureable
            destination_path = os.path.join(base_dir, str(self.camera_id),'Ambigious')
            if not os.path.exists(destination_path):
                os.makedirs(destination_path)

            if self.video_path is not None:
                new_video_path =  os.path.join(destination_path, f'{self.start_time.replace(":","_")}.mp4')
                shutil.move(self.video_path, new_video_path)
        
        # Updating the video path of the event
        if self.video_path is not None:
            self.video_path = new_video_path
