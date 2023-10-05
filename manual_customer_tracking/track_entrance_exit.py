import cv2
import pickle
import os
from typing import Tuple
import pickle
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from argparse import ArgumentParser

from get_ts_file import get_latest_file, merge_ts_files

class ManualCustTracker:

    def __init__(self, stream_path: str, camera_no: int) -> None:
        self.stream_path = stream_path
        self.camera_no = camera_no

        self.entrance_btn= [(100, 600), (300, 650)]
        self.exit_btn = [(900, 600), (1100, 650)]

        self.out = {
            "entrance": None,
            "exit": None
            }
        self.current_timestamp = None

    def show_info(self, frame):
        cv2.rectangle(frame, self.entrance_btn[0], self.entrance_btn[1], (128, 128, 128), -1)   # entrance button
        cv2.putText(frame, "entry", ((self.entrance_btn[0][0] + self.entrance_btn[1][0]) // 2, (self.entrance_btn[0][1] + self.entrance_btn[1][1]) // 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.rectangle(frame, self.exit_btn[0], self.exit_btn[1], (128, 128, 128), -1)   # exit button
        cv2.putText(frame, "exit", ((self.exit_btn[0][0] + self.exit_btn[1][0]) // 2, (self.exit_btn[0][1] + self.exit_btn[1][1]) // 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("window", frame)

    def click_event(self, event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.check_intersection(x, y)

    def check_intersection(self, x, y):
        point = Point(x, y)

        entrance_polygon = Polygon([
                                    [self.entrance_btn[0][0], self.entrance_btn[0][1]], [self.entrance_btn[1][0], self.entrance_btn[0][1]], 
                                    [self.entrance_btn[1][0], self.entrance_btn[1][1]], [self.entrance_btn[0][0], self.entrance_btn[1][1]]
                            ])

        exit_polygon = Polygon([
                                    [self.exit_btn[0][0], self.exit_btn[0][1]], [self.exit_btn[1][0], self.exit_btn[0][1]], 
                                    [self.exit_btn[1][0], self.exit_btn[1][1]], [self.exit_btn[0][0], self.exit_btn[1][1]]
                            ])
        
        if entrance_polygon.contains(point):
            # alert for entrance time is generated
            self.out["entrance"] = get_latest_file(counter_no = self.camera_no)

        elif exit_polygon.contains(point):
            # alert for exit time is generated
            self.out["exit"] = get_latest_file(counter_no = self.camera_no)

            if self.out['entrance'] is None:
                return "start or end is null"
            
            with open("intrusion_timestamp.pickle", "rb") as f:
                intTS = pickle.load(f)
            
            total_files = len(intTS)
            intTS[total_files] = (self.out["entrance"], self.out["exit"], self.camera_no)

            with open("intrusion_timestamp.pickle", "wb") as f:
                pickle.dump(intTS, f)

            self.out["entrance"] = None
            self.out["exit"] = None

    def track_customer(self):

        cap = cv2.VideoCapture(self.stream_path)

        if (cap.isOpened() == False):
            print("Error opening stream")

        frame_cnt = 0
        FPS = cap.get(cv2.CAP_PROP_FPS)

        while cap.isOpened():
            ret, frame = cap.read()
            # frame_resize = cv2.resize(frame, (1280, 720))
            frame_resize = frame.copy()
            if ret:
                
                self.current_timestamp = int(frame_cnt / FPS)    # current time in seconds
                self.show_info(frame_resize)
                cv2.setMouseCallback('window', self.click_event)
                if cv2.waitKey(25) & 0xFF == ord('q'):
                    break
            frame_cnt += 1

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":

    parser = ArgumentParser(description = "SAI manual customer tracker")
    parser.add_argument("-c", "--cam", required = True, help = 'camera number')

    args = vars(parser.parse_args())

    stream = f'rtsp://admin:Admin123@192.168.0.{args["cam"]}:554/axis-media/media.amp'
    tracker = ManualCustTracker(stream, args["cam"])
    tracker.track_customer()