import os
import datetime
import cv2
import logging
import numpy as np
import torch

from pathlib import Path
from PIL import Image
from shapely.geometry import Polygon
from moviepy.config import get_setting
from moviepy.tools import subprocess_call
from torchvision.ops.boxes import box_convert as torch_box_convert
from skimage.metrics import structural_similarity


def ts_to_strtime(ts: float) -> str:
    """
    Converts timestamp to time and returns time in %H:%M:%S format as str

    Parameters
    ----------
    ts : float
        timestamp

    Returns
    -------
    str
    """

    time_ts = (datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc) + 
                datetime.timedelta(seconds=ts)).time()
    return time_ts.strftime("%H:%M:%S")


def draw_polygon(pic, pts, color=(0, 255, 0)):
    """
    Annotates the polygon on the image.
    
    Parameters
    ----------
    pic : numpy.ndarray
        Image as numpy array.
    pts : list or iterable
        Colection of points as polygon 
    color : tuple
        Color of the polygon

    Returns
    -------
    numpy.ndarray
    A new annotated image
    """
    
    if type(pts) is dict:
        pts_arr = pts.values()
    else:
        pts_arr = [pts]

    for pts in pts_arr:
        pts = np.array(pts, np.int32)
        pts = pts.reshape((-1, 1, 2))
        isClosed = True
        thickness = 2
        image = cv2.polylines(pic, [pts],
                              isClosed, color,
                              thickness)

    return image


def annotate_boxes(img, bboxes):
    """
    Annotates the given bounding boxes on the given image.

    Parameters
    ----------
    img : numpy.ndarray
        Image as numpy array.
    bboxes : list or iterable
        Colection of boxes in xyxy format 

    Returns
    -------
    numpy.ndarray
    A new annotated images
    """
    
    for i, box in enumerate(bboxes):
        x1, y1, x2, y2 = box
        color = (0,255,0)
        label = ""
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 2, 2)[0]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        cv2.rectangle(img, (x1, y1), (x1 + t_size[0] + 3, y1 + t_size[1] + 4), color, -1)
        cv2.putText(img, label, (x1, y1 + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 1, [255, 255, 255], 2)
    return img

def create_dilated_inverted_mask(img, kernal_size=5, iterations=2, guassian_size=3):
    """Dialated inverted mask of the image"""

    img = cv2.GaussianBlur(img, (guassian_size, guassian_size), 0)
    img = cv2.Canny(img, 120, 255, 1)
    kernel = np.ones((kernal_size, kernal_size), np.uint8)
    dilate = cv2.dilate(img, kernel=kernel, iterations=iterations)
    cv2.bitwise_not(dilate, dilate)
    return dilate   


# it receives boundedRect in xywh format and returns if it lies in till area or not
def bbox_in_aisle_region(bbox, aisle_regions):
    """
    Checks if bounding box is in any of the aisle region

    Parameters
    ----------
    bbox : list or tuple
        Single bounding box in xywh format.
    aisle_regions: dict
        Dictionary of polygons as aisle regions.
    
    Returns
    -------
    bool
    """
    
    x1,y1,x2,y2 = torch_box_convert(torch.Tensor(bbox),'xywh', 'xyxy')
    item_area = Polygon([[x1, y1],  [x1, y2], 
                        [x2, y2],  [x2, y1], [x1, y1]])
    for r in aisle_regions:
        if Polygon(aisle_regions[r]).contains(item_area):
            return True
    return False


# it receives boundedRect in xywh format and returns if it lies in till area or not
def bbox_in_aisle_region_key(bbox, aisle_regions):
    """
    Checks if bounding box is in any of the aisle region

    Parameters
    ----------
    bbox : list or tuple
        Single bounding box in xywh format.
    aisle_regions: dict
        Dictionary of polygons as aisle regions.
    
    Returns
    -------
    bool
    """
    
    x1,y1,x2,y2 = torch_box_convert(torch.Tensor(bbox),'xywh', 'xyxy')
    item_area = Polygon([[x1, y1],  [x1, y2], 
                        [x2, y2],  [x2, y1], [x1, y1]])
    for r in aisle_regions:
        if Polygon(aisle_regions[r]).contains(item_area):
            return r
    return None



def filter_sized_boxes(frame_shape, contours, percentage, options="higher"):
    '''
    Args:
        frame: img
        contours: countours list
        percentage: the percentage to filter
    Returns:
        filtered countour >= percentage
    '''
    frame_area = frame_shape[0] * frame_shape[1]
    if options == "lower":
        filtered_ctrs = [ctr for ctr in contours if round((cv2.contourArea(ctr) / frame_area) * 100, 3) <= percentage]
    elif options == "higher":
        filtered_ctrs = [ctr for ctr in contours if round((cv2.contourArea(ctr) / frame_area) * 100, 3) >= percentage]
    else:
        filtered_ctrs = [ctr for ctr in contours if round((cv2.contourArea(ctr) / frame_area) * 100, 3) >= percentage[0] and round((cv2.contourArea(ctr) / frame_area) * 100, 3) <= percentage[1]]
    for c in filtered_ctrs:
        logging.info(f"Contour Area: {cv2.contourArea(c)}/{frame_area}")
    return filtered_ctrs

def get_diff_contours(start_frame, end_frame, aisle_regions, area_percentage):
    """
    Finds the difference between 2 frames and returns the contours 
    where images differ and contours inside any of the aisle region

    Parameters
    ----------
    start_frame : numpy.ndarray
        Initial frame at the start of interaction event.
    end_frame : numpy.ndarray
        Frame at the end of interaction event.
    aisle_regions: dict
        Dictionary of polygons as aisle regions.
    
    Returns
    -------
    list of contours
    """
    
    # Convert images to grayscale
    before_gray = cv2.cvtColor(start_frame, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(end_frame, cv2.COLOR_BGR2GRAY)

    # Compute SSIM between two images
    (score, diff) = structural_similarity(before_gray, after_gray, full=True)
    # diff=cv2.absdiff(before_gray, after_gray)
    # print("Image similarity", score)

    # The diff image contains the actual image differences between the two images
    # and is represented as a floating point data type in the range [0,1]
    # so we must convert the array to 8-bit unsigned integers in the range
    # [0,255] before we can use it with OpenCV
    diff = (diff * 255).astype("uint8")

    # if before_gray.shape[1]>=1200:
    #     min = 650
    #     max = 30000
    # else:
    #     min = 30
    #     max = 800
    # cv2.imshow("abc", diff)
    # cv2.waitKey(0)
    # Threshold the difference image, followed by finding contours to
    # obtain the regions of the two input images that differ
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    # cv2.imshow("abcd", thresh)
    # cv2.waitKey(0)
    contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    # diff_contours = []
    # for c in contours:
    #     area = cv2.contourArea(c)
    #     if area > min and area < max:
    #         xywh = cv2.boundingRect(c)
    #         # IOU 0 means no overlapping at all
    #         if bbox_in_aisle_region(xywh,aisle_regions):
    #             diff_contours.append(c)
    #             logging.info(f"Contour Area: {cv2.contourArea(ctr)}")

    diff_contours = []
    for c in contours:
        xywh = cv2.boundingRect(c)
        if bbox_in_aisle_region(xywh,aisle_regions):
            diff_contours.append(c)

    return filter_sized_boxes(before_gray.shape, diff_contours, area_percentage, options="between")

def create_interaction_montage(start_frame, end_frame, interaction_contours):
    """
    Creates a visualization of the interaction concatinating 4 frames.
        1 with start_frame annotated with interation contour bounding boxes
        2 with end_frame annotated with interation contour bounding boxes
        3 with black mask annotated with interation contours
        4 with end_frame annotated with interation contours
    
    Parameters
    ----------
    start_frame : numpy.ndarray
        Initial frame at the start of interaction event.
    end_frame : numpy.ndarray
        Frame at the end of interaction event.
    interaction_contours : list of contours
        Contours of the interactions

    Returns
    -------
    numpy.ndarray
    A new annotated images
    """
    
    start_frame = cv2.cvtColor(start_frame, cv2.COLOR_BGR2RGB)
    end_frame = cv2.cvtColor(end_frame, cv2.COLOR_BGR2RGB)

    mask = np.zeros(start_frame.shape, dtype='uint8')
    filled_after = end_frame.copy()

    for c in interaction_contours:
        x,y,w,h = cv2.boundingRect(c)
        cv2.rectangle(start_frame, (x, y), (x + w, y + h), (36,255,12), 2)
        cv2.rectangle(end_frame, (x, y), (x + w, y + h), (36,255,12), 2)
        cv2.drawContours(mask, [c], 0, (0,255,0), -1)
        cv2.drawContours(filled_after, [c], 0, (0,255,0), -1)

    numpy_horizontal_concat1 = np.concatenate((start_frame, end_frame), axis=1)
    numpy_horizontal_concat2 = np.concatenate((mask, filled_after), axis=1)
    numpy_vertical = np.concatenate((numpy_horizontal_concat1, numpy_horizontal_concat2), axis=0)

    img = numpy_vertical[:, :, ::-1]

    return img