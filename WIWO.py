import os
from threading import Thread

import cv2
import numpy as np
import datetime
import logging 
import time

from utilities.polygon_manager import PolygonManager

from stream_handlers.stream_handler import InputStreamHandler
from modules.shopper_interaction import ShopperInteractionDetector
from detectors.openvino_detector import OpenVino_Detector
from detectors.yolo_detector import Yolo_Detector
from trackers.sort_tracker import Sort_Tracker
from trackers.deepsort_tracker import DeepSort_Tracker
from utilities.inference_database import Inference_Database
# from utilities.mysql_uploader import MySQLUploader
from utilities.util_functions import annotate_boxes, draw_polygon
from fetch_smart_store_info import SAISmartStoreDB

def without_keys(d, keys):
    return {k: v for k, v in d.items() if k not in keys}

def get_crop_boxes(stream):

    pm = PolygonManager(stream)

    try:
       polygons = pm.get_points()
    except IndexError:
        pm.draw()

    polygons = pm.get_points()
    
    return polygons['Aisle'], without_keys(polygons, {'Aisle'})

# TODO: Come up with better idea for config handling
class WIWO:
    """
    This class implements the processing pipeline at higher level.
    """
    
    def __init__(self, config) -> None:
        self.config = config
        self.frame_skip = config['shopper_interaction']['frames_skip']

        # Events/Destination path
        todays_date = datetime.datetime.now().date().strftime("%Y-%m-%d")
        self.events_destination_path = os.path.join(os.getcwd(), config['output_folder'], f"{todays_date}")
        self.events_database = Inference_Database(self.events_destination_path)

        # self.smart_store_db = SAISmartStoreDB(config_file='config.json')

    def _get_aisle_regions(self, streams):
        aisle_regions = {}
        crop_regions = {}
        for stream in self.config['input_streams']['sources']:
            # _, regions = self.smart_store_db.get_aisles_blocks_sections(stream['camera_id'])
            # print(stream["crop_labels"], regions)
            # stream["crop_labels"] = regions
            till_area_points, crop_region = get_crop_boxes(stream)
            aisle_regions[stream['camera_id']] = {'r1': till_area_points}
            crop_regions[stream['camera_id']] = crop_region 
        # pm = PolygonManager()
        # aisle_regions = {}
        # for src in streams:
        #     try:
        #         till_area_points = pm.get_polygon_points(str(src.camera_id), resize=src.frame_size[:2])
        #     except Exception as e:
        #         pm.create_new_polygon(str(src.camera_id), src.source)
        #         till_area_points = pm.get_polygon_points(str(src.camera_id), resize=src.frame_size[:2])

        #     aisle_regions[src.camera_id] = {'r1': till_area_points}

        return aisle_regions, crop_regions

    def _initialize_detector(self, config):
        if config['processing_mode'] == 'OPENVINO':
            detector = OpenVino_Detector(**config['openvino'])
        elif config['processing_mode'] == 'YOLO':
            detector = Yolo_Detector(**config['yolo'])
        #TODO: handle else case
        return detector

    def _initialize_trackers(self, config, camera_ids):
        trackers = {}
        for cam in camera_ids:
            if config['type'] == 'SORT':
                trackers[cam] = Sort_Tracker(**config['sort'])
            elif config['type'] == 'DEEPSORT':
                trackers[cam] = DeepSort_Tracker()
            #TODO: handle else case
        return trackers

    def _initialize_interaction_detectors(self, config, streams, aisle_regions, crop_regions):
        interaction_detectors = {}
        for stream in streams:
            interaction_detectors[stream.camera_id] = \
                ShopperInteractionDetector( config,
                                            aisle_regions[stream.camera_id],
                                            stream.fps, stream.frame_size[:2],
                                            stream.camera_id, crop_regions)
        return interaction_detectors

    def start(self):
        # mysql_uploader = MySQLUploader()
        stream_handler = InputStreamHandler(**self.config['input_streams'])
        stream_handler.start()

        aisle_regions, crop_regions = self._get_aisle_regions(stream_handler.streams)
        camera_ids = [stream.camera_id for stream in stream_handler.streams]

        detector = self._initialize_detector(self.config['detector'])
        trackers = self._initialize_trackers(self.config['tracker'], camera_ids)

        interaction_detectors = self._initialize_interaction_detectors(self.config, stream_handler.streams, aisle_regions, crop_regions)
        
        for frame_id, timestamps, imgs in stream_handler:
            
            processing_time_start = time.time()

            # print(frame_id, [im.dtype if im is not None else None for im in imgs])

            imgs_replaced_nones = [img if img is not None 
                                        else np.zeros((stream_handler.streams[i].frame_size[1],
                                                        stream_handler.streams[i].frame_size[0],
                                                        stream_handler.streams[i].frame_size[2]), dtype=np.uint8) 
                                            for i, img in enumerate(imgs)]

            # print(frame_id, [im.dtype for im in imgs_replaced_nones])
            
            if frame_id % self.frame_skip == 0:

                preds = detector.infer(imgs_replaced_nones)

                logging.info("Detections --> " + str(preds))

                tracks = {}
                for cam_id, img, pred in zip(camera_ids, imgs, preds):
                    if img is not None:
                        tracks[cam_id] = trackers[cam_id].update(pred, img)
                
                logging.info("Tracks --> " + str(tracks))

                interaction_events = {}
                for cam_id, timestamp, img, trk, in zip(tracks.keys(),timestamps, imgs,tracks.values()):
                    if img is not None:
                        interaction_events[cam_id] = interaction_detectors[cam_id].check_interacion(timestamp, img, trk)

                logging.info("Events --> " + str(interaction_events))

                for cam_id, event in interaction_events.items():
                    if event is not None:
                        event.determin_crop_region(crop_regions[event.camera_id])
                        event.save_files(self.events_destination_path)
                        if event.interactions_count > 0:
                            todays_date = datetime.datetime.now().date().strftime("%Y_%m_%d")
                            # store_id = self.config['store_id']
                            # file_cloud_name = f"{store_id}_{cam_id}_{todays_date}_{event.start_time.replace(':','_')}.mp4"
                            # file_path = os.path.join(self.events_destination_path, str(cam_id), f"{event.start_time.replace(':','_')}.mp4")
                            # vid_uploading_thread = Thread(target=az_uploader.upload_to_blob_storage,
                            #                               args=(file_path, file_cloud_name), daemon=True)
                            # vid_uploading_thread.start()

                            # # Uploading the meta and name of video in central db
                            # meta_uploading_thread = Thread(target=mysql_uploader.upload_video_name,
                            #                               args=(store_id, cam_id, datetime.datetime.now().date().strftime("%Y-%m-%d"),event.start_time ), daemon=True)
                            # meta_uploading_thread.start()
                        self.events_database.add_shopper_interaction_event(event)
      
                logging.info(f"Stream time: {0}, " + \
                        f"System Frame processing Time: {int((time.time() - processing_time_start)*1000)}ms")
                
                if self.config['display_result']:
                    for cam_id, img, trk, in zip(tracks.keys(),imgs,tracks.values()):
                        if img is not None:
                            # if trk.shape[0] > 0:
                                # bboxes = trk[:,:4].tolist()
                                # print(i, bboxes)
                                # img = annotate_boxes(img.copy(), bboxes)
                            img_ = draw_polygon(img.copy(), aisle_regions[cam_id] | crop_regions[cam_id])
                            cv2.imshow(str(cam_id), img_)

                now_dt = datetime.datetime.now()
                end_dt = datetime.datetime.strptime(self.config['end_processing_time'], "%H:%M:%S")
                if now_dt.time() >= end_dt.time():
                    break

            if cv2.waitKey(1) == ord('q'):  # q to quit
                break


        self.events_database.save_into_csv()
        cv2.destroyAllWindows()
