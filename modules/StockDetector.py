from cv2 import cv2
from Settings.Constants import Constants
from config import EMPTY_STOCK_BOX_SIZE_IN_PERCENT,PARTIALLY_EMPTY_STOCK_BOX_SIZE_IN_PERCENT
from utilities.util_functions import filter_aisle_rects, draw_contours, get_white_percentage, \
    filter_sized_boxes, create_dilated_inverted_mask, save_frame, draw_polygon
from statistics import mode, StatisticsError
from collections import Counter
from itertools import groupby
from threading import Thread


class StockDetector:
    till_area = None

    def __init__(self, till_area):
        self.till_area = till_area

    def filter_plain_boxes(self, mask, size_prcentage=EMPTY_STOCK_BOX_SIZE_IN_PERCENT, white_threshold=70, condition='higher'):
        '''
        Description:
            It will receive a mask and  will return rectangles with major white area
        Args:
            mask: dilated & inverted mask
            threshold: it will be used as white area percentage in contour/rectangle
        Returns:
            ctrs: array of boxes which contains specific amount of white pixels
        '''
        ctrs = []

        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contours = contours[0] if len(contours) == 2 else contours[1]
        empty_contours = filter_sized_boxes(frame=mask, contours=contours,
                                      percentage=size_prcentage,
                                      options=condition)


        for i in range(0, len(empty_contours)):
            percentage = get_white_percentage(mask, empty_contours[i])
            if percentage >= white_threshold:
                ctrs.append(empty_contours[i])
        return ctrs

    def get_stock_boxes(self, frame):
        mask = create_dilated_inverted_mask(frame, kernal_size=5, iterations=4)
        empty_boxes = self.filter_plain_boxes(mask, size_prcentage=EMPTY_STOCK_BOX_SIZE_IN_PERCENT, condition='higher')
        partially_empty_boxes = self.filter_plain_boxes(mask, white_threshold=60,size_prcentage=PARTIALLY_EMPTY_STOCK_BOX_SIZE_IN_PERCENT, condition='between')
        empty_boxes = filter_aisle_rects(self.till_area, empty_boxes)
        partially_empty_boxes = filter_aisle_rects(self.till_area, partially_empty_boxes)
        partially_empty_boxes = [p for p in partially_empty_boxes if cv2.boundingRect(p)[3] > 50]
        # print(len(empty_boxes))
        # show_img('mask', mask)
        return empty_boxes,partially_empty_boxes

    def calculate_mode_idx(self,stock_arr ):
        stock_count_arr = [len(arr) for arr in stock_arr]
        try:
            empty_stock_count = mode(stock_count_arr)
        except StatisticsError as e:
            empty_stock_count = 0
            freqs = groupby(Counter(stock_count_arr).most_common(), lambda x: x[1])
            mode_arr = [val for val, count in next(freqs)[1]]
            if len(mode_arr) > 0:
                empty_stock_count = mode_arr[0]

        e_idx = stock_count_arr.index(empty_stock_count)
        return empty_stock_count, e_idx

    def get_accumulative_empty_stocks(self,  empty_stock_arr, partial_stock_arr):
        '''
        Description:
            It will receive array of arrays of boxes on N frames
            and calculate Mode for the accurate count of empty boxes
        Args:
            empty_stock_arr: nested array of contours which are considered as out of stock boxes
            partial_stock_arr: nested array of contours which are considered as low stock boxes
        Returns:
            empty_stock_arr: array of empty bounding boxes
            partial_stock_arr: Array of partially empty bounding boxes
        '''
        if len(empty_stock_arr) > 0:
            empty_stock_count, e_idx = self.calculate_mode_idx(empty_stock_arr)
            empty_stock_array = empty_stock_arr[e_idx]
        else:
            empty_stock_array = []

        if len(partial_stock_arr) > 0:
            partial_stock_count, p_idx = self.calculate_mode_idx(partial_stock_arr)
            partial_stock_array = partial_stock_arr[p_idx]
        else:
            partial_stock_array = []

        return empty_stock_array,partial_stock_array

    def save_stock_detection_image(self, frame, path, time_stamp, empty_stocks, partial_stocks):
        stock_draw_img = frame.copy()
        stock_draw_img = draw_polygon(stock_draw_img, self.till_area, Constants.YELLOW)
        stock_draw_img = cv2.cvtColor(stock_draw_img, cv2.COLOR_BGR2RGB)
        stock_draw_img = self.draw_stocks(stock_draw_img, empty_stocks, partial_stocks)
        t1 = Thread(target=save_frame, args=(path,stock_draw_img,time_stamp), daemon=True)
        t1.start()
        return stock_draw_img

    def draw_stocks(self, frame,empty_stock_arr,partial_stock_arr ):
        cv2.putText(frame, str(f"Empty Shelves: {len(empty_stock_arr)}"), (50, 50),
                    fontFace=cv2.FONT_HERSHEY_PLAIN,
                    fontScale=2,
                    color=Constants.GREEN, thickness=3)
        cv2.putText(frame, str(f"Low Stock Shelves: {len(partial_stock_arr)}"), (50, 80),
                    fontFace=cv2.FONT_HERSHEY_PLAIN,
                    fontScale=2,
                    color=Constants.GREEN, thickness=3)
        if len(empty_stock_arr) > 0 or len(partial_stock_arr) > 0:
            frame = draw_contours(frame, empty_stock_arr, color=Constants.BLUE)
            frame = draw_contours(frame, partial_stock_arr, color=Constants.RED)

        return frame





