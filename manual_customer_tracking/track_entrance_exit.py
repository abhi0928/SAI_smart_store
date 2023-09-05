import cv2
import pickle
import os
from typing import Tuple
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon



class ManualCustTracker:

    def __init__(self, stream_path: str):
        self.stream_path = stream_path

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
            self.out["entrance"] = self.current_timestamp

        elif exit_polygon.contains(point):
            # alert for exit time is generated
            self.out["exit"] = self.current_timestamp
            
            # TODO-> video creation code will run
            print(self.out)
            exit(1)


    def track_customer(self):

        cap = cv2.VideoCapture(self.stream_path)

        if (cap.isOpened() == False):
            print("Error opening stream")

        frame_cnt = 0
        FPS = cap.get(cv2.CAP_PROP_FPS)

        while cap.isOpened():
            ret, frame = cap.read()
            # print(frame.shape)
            # frame_resize = cv2.resize(frame, (1280, 720))
            frame_resize = frame.copy()
            if ret:
                
                self.current_timestamp = int(frame_cnt / FPS)    # current time in seconds
                # cv2.imshow('window', frame)
                self.show_info(frame_resize)
                cv2.setMouseCallback('window', self.click_event)
                if cv2.waitKey(25) & 0xFF == ord('q'):
                    break
            frame_cnt += 1

        cap.release()
        cap.destroyAllWindows()


if __name__ == "__main__":

    tracker = ManualCustTracker("demo.mp4")
    tracker.track_customer()
