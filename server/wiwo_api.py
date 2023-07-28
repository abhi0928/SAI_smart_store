import os
from datetime import datetime
import base64
import requests
from cv2 import cv2
from config import STORE_ID, CAMERA_TO_AISLE_ID_MAPPING, SYSTEM_PROXY
from dotenv import load_dotenv
load_dotenv()
class WiwoApi:
    def update_out_of_stock_table(self, camera_no, flag, frame=None):
        '''
        Description:
                It updates the entry in central database by calling the API
        Args:
            camera_no: The ip of camera feed
            flag: 0 for empty stock , 1 for non-empty stock
            frame: the drawn picture with empty stock indications

        Returns:
            True/False  based on upadte given by database

        '''
        retval, buffer_img = cv2.imencode('.jpg', frame)
        encoded_image = base64.b64encode(buffer_img).decode('utf-8')

        headers = {'accept': '*/*',
                   'content-type': 'application/json',
                   'user-agent': 'XY'}

        proxies = {
            'http':SYSTEM_PROXY,
            'https':SYSTEM_PROXY,
        }

        data = {'sroreId': STORE_ID,
                'aisleId': CAMERA_TO_AISLE_ID_MAPPING[str(camera_no)],
                'cameraNo': camera_no,
                'flag': flag,
                'dateTime':str(datetime.now()),
                'image':str(encoded_image)
                }
        stock_route = f"{os.getenv('BASE_LINK')}/{os.environ.get('STOCK_ROUTE')}"
        # resp = requests.request('POST', Routes.STOCK_ROUTE, json=data, headers=headers, proxies=proxies)
        resp = requests.request('POST', stock_route, json=data, headers=headers)
        print("\n", resp.status_code, "====================  Stock API Response")
        if resp.status_code is 200:
            return True
        return False


    def update_clutter_info(self, camera_no, flag, frame=None):
        '''
        Description:
                It updates the entry in central database by calling the API
        Args:
            camera_no: The ip of camera feed
            flag: 0 for empty stock , 1 for non-empty stock
            frame: the drawn picture with clutter indication

        Returns:
            True/False  based on upadte given by database

        '''

        retval, buffer_img = cv2.imencode('.jpg', frame)
        str_encode = buffer_img.tobytes()
        encoded_image = base64.b64encode(str_encode)
        encoded_image = encoded_image.decode("utf-8")

        headers = {'accept': '*/*',
                   'content-type': 'application/json',
                   'user-agent': 'XY'}

        proxies = {
            'http': SYSTEM_PROXY,
            'https': SYSTEM_PROXY,
        }

        data = {'storeId': STORE_ID,
                'aisleId': CAMERA_TO_AISLE_ID_MAPPING[str(camera_no)],
                'cameraNo': camera_no,
                'flag': flag,
                'dateTime': str(datetime.now()),
                'image': encoded_image
                }

        clutter_route = f"{os.getenv('BASE_LINK')}/{os.environ.get('CLUTTER_ROUTE')}"

        # resp = requests.request('POST', Routes.CLUTTER_ROUTE, json=data, headers=headers, proxies=proxies)
        resp = requests.request('POST', clutter_route, json=data, headers=headers)
        print("\n", resp.status_code, "====================  Clutter API Response")
        if resp.status_code is 200:
            return True

        return False
