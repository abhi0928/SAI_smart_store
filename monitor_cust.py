import numpy as np
import cv2
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import pickle
from fetch_smart_store_info import SAISmartStoreDB




class MonitorCust:

    def __init__(self, store_name : str, aisle_name: str, regions_file : str, db_config_file : str) -> None:
        self.store_name = store_name
        self.aisle_name = aisle_name
        self.regions = pickle.load(open(regions_file, 'rb'))
        self.smart_store_db = SAISmartStoreDB(store_name = self.store_name, config_file = db_config_file)
        self.info_table = {"current_selection" : None, "total_bill" : None}
        self.x = None
        self.y = None
        self.current_aisle = None
        self.current_item_price = None
        self.current_item_name = None
        self.total_bill = 0

    def show_info(self, frame):
        if self.current_aisle != None:
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.rectangle(frame, (self.x - 10, self.y - 30), (self.x + 250, self.y + 35), (128, 128, 128), -1)
            cv2.putText(frame, f'Item: {self.current_item_name}', (self.x, self.y), font, 
                        1, (255, 0, 0), 2)
            cv2.putText(frame, f'Price: {self.current_item_price}', (self.x, self.y + 30), font,
                        1, (48, 25, 52), 2)
        cv2.imshow('image', frame)

    def click_event(self, event, x, y, flags, params):

        if event == cv2.EVENT_LBUTTONDOWN:
            # print(x, ' ', y)
            self.x = x
            self.y = y
            status, self.current_aisle = self.check_intersection(x, y, self.regions[128])
            if status:
                self.current_item_name, self.current_item_price = self.smart_store_db.fetch_item_info(aisle_name = self.aisle_name, block_name = self.current_aisle)

            # if event == cv2.EVENT_RBUTTONDOWN:
        
            #     # print(x, ' ', y)
            #     return x, y
            
    
    def check_intersection(self, x, y, regions):
        point = Point(x, y)
        for region, aisle in zip(regions['polygon'].values(), regions['stream']['crop_labels']):
            if aisle == 'Aisle':
                continue
            polygon = Polygon(region)
            if polygon.contains(point):
                return (True, aisle)
        return (False, None)

                    
    def run(self, stream):
        cap = cv2.VideoCapture(stream)

        if (cap.isOpened() == False):
            print("Error opening video file")

        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame_resize = cv2.resize(frame, (1280, 720))

                # cv2.imshow('image', frame_resize)
                self.show_info(frame = frame_resize)

                cv2.setMouseCallback('image', self.click_event)
                # process on frame

                if cv2.waitKey(25) & 0xFF == ord('q'):
                    break
            else:
                break

        cap.release()
        cv2.destroyAllWindows()




# if __name__=="__main__":

#     monitor = MonitorCust(store_name = 'store1', aisle_name = 'aisle_128', regions_file = '../polygons_config.pkl',
#                           db_config_file = 'config.json')
#     monitor.run('../archway/128.mp4')
