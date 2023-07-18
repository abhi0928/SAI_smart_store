import numpy as np
import cv2
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import requests
import pickle
import csv
# from fetch_smart_store_info import SAISmartStoreDB
from transactions import get_transaction_id, add_transactions
from test_checkout import CheckoutUpdate
import argparse
import ast
from typing import List

class MonitorCust:

    def __init__(self, store_name : str, aisle_name : str, transaction_id : int, stream : str = None, regions_file : str = 'archway_aisle_map.pkl',
                                 db_config_file : str = 'config.json', rtsp : bool = False) -> None:
        self.store_name = store_name
        self.aisle = aisle_name
        self.transaction_id = transaction_id
        self.aisle_name = f'aisle_{aisle_name}'
        self.regions = pickle.load(open(regions_file, 'rb'))
        # self.smart_store_db = SAISmartStoreDB(store_name = self.store_name, config_file = db_config_file)
        if rtsp:
            self.stream = f'rtsp://admin:Admin123@192.168.1.{self.aisle}:554/Streaming/Channels/101'
        else:
            self.stream = stream
        self.prod_list = {}
        self.x = None
        self.y = None
        self.current_aisle = None
        self.current_item_id = None
        self.current_item_price = None
        self.current_item_name = None
        self.total_bill = 0
        self.checkout_status = False

    def generate_invoice(self):
        # tran_id = get_transaction_id()

        for prod, info in self.prod_list.items():
            add_transactions(self.transaction_id, info[3], info[1])

        total_products = sum([i[1] for i in self.prod_list.values()])
        with open("demo_invoice.csv", 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Product_name', 'Product_price', 'Quantity', 'Total_price'])
            for prod, info in self.prod_list.items():
                writer.writerow([prod, info[0], info[1], info[2]])
            writer.writerow(['', '', '', ''])
            writer.writerow(['Total', '', total_products, self.total_bill])
        print("Invoice generated")

    def get_item_info(self):
        block = 'block' + self.current_aisle[0]
        section = 'section' + self.current_aisle
        params = {
            "section" : section,
            "block" : block,
            "aisle" : self.aisle_name,
            "store" : self.store_name
        }
        
        response = requests.get(
                'http://51.132.13.113:8001/get_item_id',
                params = params
        )

        res = ast.literal_eval(response.text)
        return res[0]["item_id"], res[0]["name"], res[0]["price"]

    def show_bill_info(self, frame, font):
        try:
           # current item name
            cv2.rectangle(frame, (600, 670), (1050, 720), (91, 91, 91), -1)
            cv2.putText(frame, f"count/total_price : {self.prod_list[self.current_item_name][0]}/{self.prod_list[self.current_item_name][1]}", (610, 700),
                        font, 1, (44, 250, 234), 2)

            cv2.rectangle(frame, (1000, 670), (1250, 720), (128, 128, 128), -1)
            cv2.putText(frame, f"Total : {self.total_bill}", (1010, 700), font,
                        1, (234, 250, 44), 2)
        except:
            pass
    

    def show_buttons(self, frame, font):
        cv2.rectangle(frame, (20, 670), (100, 720), (128, 128, 128), -1)
        cv2.putText(frame, "+", (50, 700), font, 1, (44, 250, 234), 2)

        cv2.rectangle(frame, (120, 670), (200, 720), (128, 128, 128), -1)
        cv2.putText(frame, "-", (150, 700), font, 1, (44, 250, 234), 2)

        cv2.rectangle(frame, (220, 670), (380, 720), (128, 128, 128), -1)
        cv2.putText(frame, "submit", (250, 700), font, 1, (44, 250, 234), 2)

    def show_info(self, frame):
        font = cv2.FONT_HERSHEY_SIMPLEX
        if self.checkout_status:
            cv2.rectangle(frame, (400, 670), (600, 720), (91, 91, 91), -1)
            cv2.putText(frame, f"CHECKOUT", (410, 700),
                        font, 1, (0, 0, 255), 2)
        if self.current_aisle != None:
            cv2.rectangle(frame, (self.x - 10, self.y - 30), (self.x + 250, self.y + 35), (128, 128, 128), -1)
            cv2.putText(frame, f'Item: {self.current_item_name}', (self.x, self.y), font, 
                        1, (255, 0, 0), 2)
            cv2.putText(frame, f'Price: {self.current_item_price}', (self.x, self.y + 30), font,
                        1, (48, 25, 52), 2)
        self.show_bill_info(frame, font)
        self.show_buttons(frame, font)

        cv2.imshow('image', frame)

    def click_event(self, event, x, y, flags, params):

        if event == cv2.EVENT_LBUTTONDOWN:
            # print(x, ' ', y)
            self.x = x
            self.y = y
            status, self.current_aisle = self.check_intersection(x, y, self.regions[int(self.aisle)])
            if status:
                # self.current_item_id, self.current_item_name, self.current_item_price = self.smart_store_db.fetch_item_info(aisle_name = self.aisle_name,
                #                                                                                          block_name = self.current_aisle)
                self.current_item_id, self.current_item_name, self.current_item_price = self.get_item_info()
                if self.current_item_name not in self.prod_list.keys():
                    self.prod_list[self.current_item_name] = [self.current_item_price, 1, self.current_item_price, self.current_item_id]
                else:
                    self.prod_list[self.current_item_name][1] += 1
                    self.prod_list[self.current_item_name][2] += self.current_item_price
                self.total_bill += self.current_item_price

            # if event == cv2.EVENT_RBUTTONDOWN:
        
            #     # print(x, ' ', y)
            #     return x, y
            
    
    def check_intersection(self, x, y, regions):
        point = Point(x, y)
        # check if increment/decrement button is pressed
        if self.current_item_name != None:
            polygon1 = Polygon([[20, 670], [100, 670], [100, 720], [20, 720]])
            polygon2 = Polygon([[120, 670], [200, 670], [200, 720], [120, 720]])
            polygon3 = Polygon([[220, 670], [380, 670], [380, 720], [220, 720]])
            if polygon1.contains(point):
                self.prod_list[self.current_item_name][1] += 1
                self.prod_list[self.current_item_name][2] += self.current_item_price
                self.total_bill += self.current_item_price
            elif polygon2.contains(point):
                self.prod_list[self.current_item_name][1] -= 1
                self.prod_list[self.current_item_name][2] -= self.current_item_price
                self.total_bill -= self.current_item_price
            elif polygon3.contains(point):
                self.generate_invoice()
                import sys
                sys.exit(1)
            
        for region, aisle in zip(regions['polygon'].values(), regions['stream']['crop_labels']):
            if aisle == 'Aisle':
                continue
            polygon = Polygon(region)
            if polygon.contains(point):
                return (True, aisle)
        return (False, None)

                    
    def run(self):
        cap = cv2.VideoCapture(self.stream)

        if (cap.isOpened() == False):
            print("Error opening video file")

        cnt = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame_resize = cv2.resize(frame, (1280, 720))
                if cnt % 100 == 0:
                    checkout = pickle.load(open('checkout_status.pkl', 'rb'))
                    if checkout:
                        self.checkout_status = True

                # cv2.imshow('image', frame_resize)
                self.show_info(frame = frame_resize)

                cv2.setMouseCallback('image', self.click_event)

                if cv2.waitKey(25) & 0xFF == ord('q'):
                    break
            else:
                break

        cap.release()
        cv2.destroyAllWindows()
        self.generate_invoice()


if __name__=="__main__":

    import multiprocessing

    parser = argparse.ArgumentParser(description = "SAI smart store project demo")

    parser.add_argument("-sn", "--store", required = True, help = 'name of the store')
    parser.add_argument("-a", "--aisle", required = True, help = 'aisle which needs to monitor')
    parser.add_argument("-r", "--regions", default = 'archway_aisle_map.pkl', help = 'pickle file contain regions')
    parser.add_argument("-db", "--dbconfig", default = 'config.json', help = 'database config file')
    parser.add_argument("-s", "--stream", default = None, help = 'path of stream')
    parser.add_argument("-rt", "--rtsp", help = "url of rtsp stream")
    parser.add_argument("-t", "--tranid", help = "transaction id")

    args = vars(parser.parse_args())
    
    monitor = MonitorCust(store_name = args["store"], aisle_name = args["aisle"], transaction_id = args["tranid"], stream = args["stream"],
                            regions_file = args["regions"], db_config_file = args["dbconfig"], rtsp = args["rtsp"])
    
    monitor.run()
    