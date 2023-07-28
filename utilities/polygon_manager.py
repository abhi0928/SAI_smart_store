import os.path
import cv2
import numpy as np
import pickle
import yaml

def load_pickle(filename):
    with open(filename, 'rb') as handle:
        return pickle.load(handle)

def save_pickle(filename, data):
    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    @staticmethod
    def to_dict(d):
        if type(d) is dotdict:
            newdict = {}
            for key,val in d.items():
                newdict[key] = dotdict.to_dict(val)
            return newdict
        if type(d) is list:
            newlist = []
            for val in d:
                newlist.append(dotdict.to_dict(val))
            return newlist
        return d

    @staticmethod
    def to_dotdict(d):
        if type(d) is dict:
            newdict = {}
            for key,val in d.items():
                newdict[key] = dotdict.to_dotdict(val)
            return dotdict(newdict)
        if type(d) is list:
            newlist = []
            for val in d:
                newlist.append(dotdict.to_dotdict(val))
            return newlist
        return d


def draw_text(img, text,
        font=cv2.FONT_HERSHEY_PLAIN,
        pos=(0, 0),
        font_scale=2,
        font_thickness=2,
        text_color=(0, 0, 0),
        text_color_bg=(200, 200, 200),
        align_center=False
        ):

    x, y = pos
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_w, text_h = text_size
    if align_center:
        x = x - text_w//2
        y = y - text_h//2
    cv2.rectangle(img, (x,y), (x + text_w, y + text_h), text_color_bg, -1)
    cv2.putText(img, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)

    return text_size

def draw_polygon(img, points, label = "", show_xy=True, color=(0, 255, 255)):
    font = cv2.FONT_HERSHEY_SIMPLEX
    is_closed = True
    thickness = 2
    points = np.array(points, np.int32)
    pts = points.reshape((-1, 1, 2))
    cv2.polylines(img, [pts], is_closed, color, thickness)    
    draw_text(img, f"{label}", font, (points[0][0], points[0][1]), font_scale=1, align_center=True)

def xyxy2xywh(xyxy):
    xmin = min(xyxy[0], xyxy[2])
    ymin = min(xyxy[1], xyxy[3])
    xmax = max(xyxy[0], xyxy[2])
    ymax = max(xyxy[1], xyxy[3])
    x = int((xmin + xmax) / 2.0)
    y = int((ymin + ymax) / 2.0)
    w = xmax - xmin
    h = ymax - ymin
    return [x, y, w, h]



def draw_regions(image, camera_no, polygons_dict: dict):
    # camera_no = self.stream.camera_id
    # polygons_dict = load_pickle(self.polygons_file_name)
    # if camera_no in polygons_dict.keys():
        # image = polygons_dict[f'{camera_no}']['image']
        # stream = polygons_dict[f'{camera_no}']['stream']
        # pts  = polygons_dict[f'{camera_no}']['polygon']
    for label, points in polygons_dict.items():
        # __import__('ipdb').set_trace()
        draw_polygon(image, points, label=label)
    # else:
    #     raise Exception(f"No polygon is present for camera {camera_no}")

    return image
    # cv2.imshow(f"{camera_no}", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

class PolygonManager:
    '''
    class to manage the points for a polygon
    '''
    BOX_MODE_XYXY  = 'xyxy'
    BOX_MODE_XYWH  = 'xywh'
    FONT=cv2.FONT_HERSHEY_SIMPLEX

    def __init__(self, stream_dict, windowname="Draw Bounding Boxes:", polygons_file_name="polygons_config.pkl"):
        self.stream = dotdict.to_dotdict(stream_dict)
        self.windowname = windowname + f" {self.stream.camera_id}"

        self.points = []
        self.polygons = {}
        self.polygons_file_name = polygons_file_name
        if 'crop_labels' in self.stream:
            self.stream.crop_labels.insert(0, "Aisle")
        # if file does not exist, create one with empty dict
        if not os.path.exists(self.polygons_file_name):
            save_pickle(self.polygons_file_name,{})

    def draw(self, edit=False):
        self.frame = PolygonManager.__get_first_frame(self.stream.source)
        cv2.namedWindow(self.windowname, cv2.WINDOW_GUI_NORMAL)

        self.polygons_dict = load_pickle(self.polygons_file_name)
        if edit and self.stream.camera_id in self.polygons_dict:
            self.polygons = self.polygons_dict.get(self.stream.camera_id, {}).get('polygon',  {})

        while True:
            img = self.frame.copy()
            cv2.imshow(self.windowname, img)
            cv2.setMouseCallback(self.windowname, self.__click_event)
            keycode = cv2.waitKey(0)
            if keycode == 32: # SPACE PRESSED
                if len(self.polygons) >= len(self.stream.crop_labels):
                    self.__save_polygon()
                    break
                self.polygons[len(self.polygons)] = self.points
                self.points = []
            elif keycode == 27: # ESC PRESSED
                break

        cv2.destroyAllWindows()
    
    @staticmethod
    def __get_first_frame(videofile):
        vidcap = cv2.VideoCapture(videofile)
        success = False
        while not success:
            success, image = vidcap.read()
        if success:
            return image
        raise Exception("Could not read frame from stream.")

    def __click_event(self, event, x, y, flags, params):
        font = cv2.FONT_HERSHEY_SIMPLEX
        drawn_frame = self.frame.copy()

        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append([x, y])
        elif event == cv2.EVENT_RBUTTONDOWN:
            if len(self.points):
                self.points.pop()
            elif len(self.polygons) > 0:
                del self.polygons[len(self.polygons)-1]
        elif event == cv2.EVENT_MOUSEMOVE:
            if 'crop_labels' in self.stream:
                if len(self.polygons) >= len(self.stream.crop_labels):
                    label = "Done"
                else:
                    if len(self.points) >= 1:
                        label = f"Drawing Label: {self.stream.crop_labels[len(self.polygons)]}"
                    else:
                        label = f"Next Label: {self.stream.crop_labels[len(self.polygons)]}"
                
                draw_text(drawn_frame, label, font, (x, y), font_scale=1)

        cv2.putText(drawn_frame, "Right Click to Undo...", (10, 20), font,
                    0.5, (255, 0, 0), 2)
        cv2.putText(drawn_frame, "Press Space key to save...", (10, 40), font,
                    0.5, (255, 0, 0), 2)
        cv2.putText(drawn_frame, "Press ESC key to cancel...", (10, 60), font,
                    0.5, (255, 0, 0), 2)
        
        if len(self.points) >=1:
            x = self.points[0][0]
            y = self.points[0][1]
            draw_text(drawn_frame, str(x) + ',' + str(y), font, (x, y), font_scale=1)
            if len(self.points) >= 2:
                for i in range(1,len(self.points)):
                    x = self.points[i][0]
                    y = self.points[i][1]
                    draw_text(drawn_frame, str(x) + ',' + str(y), font, (x, y), font_scale=1)
                    drawn_frame = cv2.line(drawn_frame, tuple(self.points[i-1]), tuple(self.points[i]),color=(255, 0, 0),thickness=2)
        if len(self.polygons) >= 1:
            for indx, points in self.polygons.items():
                label=""
                if 'crop_labels' in self.stream:
                    label = f"Label: {self.stream.crop_labels[indx]},"
                draw_polygon(drawn_frame, points, label=label)

        cv2.imshow(self.windowname, drawn_frame)


    def __save_polygon(self):
        self.polygons_dict[self.stream.camera_id] = {
            'polygon': self.polygons,
            'image': self.frame,
            'stream': dotdict.to_dict(self.stream)
        }
        with open(self.polygons_file_name, 'wb') as handle:
            pickle.dump(self.polygons_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


    def get_points(self):
        """
        `normalized` and `resize` are mutually exclusive
        """
        camera_no = self.stream.camera_id
        polygons_dict = load_pickle(self.polygons_file_name)
        if camera_no in polygons_dict.keys():
            pts = polygons_dict[camera_no]['polygon']
            polygons = {}
            for i in range(len(pts)):
                polygons[polygons_dict[camera_no]['stream']['crop_labels'][i]] = pts[i]
            return polygons

        raise IndexError(f"No polygon is present for camera {camera_no}")

