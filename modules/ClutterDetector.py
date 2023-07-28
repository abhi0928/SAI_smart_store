import os
import cv2
import numpy as np
from skimage.metrics import structural_similarity
import skimage

class ClutterDetection:
    def __init__(self, crop_cordinates, base_image_path, video_path, camera_no):
        # if not os.path.exists(base_image_path):
        self.get_first_frame(video_path, camera_no)
        self.crop_cordinates = crop_cordinates
        self.base_image_path = base_image_path
        self.isClosed = True
        self.color = (255, 0, 0)
        self.thickness = 2
        self.rect = cv2.boundingRect(crop_cordinates)
        print("BASE IMG :",self.base_image_path)
        self.before = cv2.imread(base_image_path)


    def get_first_frame(self, video_path, camera_no):
        vid_cap = cv2.VideoCapture(video_path)
        start_frame_number = 0

        while True:
            # vid_cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_number)
            # start_frame_number += 1
            rval, frame = vid_cap.read()
            cv2.namedWindow("Select Frame by pressing S", cv2.WINDOW_NORMAL)
            cv2.imshow("Select Frame by pressing S", frame)
            key = cv2.waitKey(0)
            if key == ord("s"):
                cv2.imwrite('./assets/{}.jpg'.format(camera_no), frame)
                break
            if key == ord("n"):
                pass
            if key == ord("b"):
                break

        vid_cap.release()
        cv2.destroyAllWindows()

    def get_thershold_value(self,boxA, boxB):
        w1, h1 = boxA[-2], boxA[-1]
        w2, h2 = boxB[-2], boxB[-1]
        A1 = w1 * h1
        A2 = w2 * h2
        result = A1 - A2
        return {"A1": A1,
                "A2": A2,
                "Result": result,
                "Area left": result / A1, }

    def image_show(self, image):
        while True:
            cv2.imshow("T", image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

    def get_cart_info(self,frame):
        frame1 = frame

        x, y, w, h = self.rect
        image_before = cv2.rectangle(self.before, (x,y),(x+w,y+h), self.color, self.thickness)

        image_after = cv2.rectangle(frame,(x,y),(x+w,y+h), self.color, self.thickness)


        # print(self.rect)
        # print(x, y, w, h)

        before_croped = image_before[y:y + h, x:x + w].copy()
        after_cropped = image_after[y:y + h, x:x + w].copy()

        # Convert images to grayscale
        before_gray = cv2.cvtColor(before_croped, cv2.COLOR_BGR2GRAY)
        after_gray = cv2.cvtColor(after_cropped, cv2.COLOR_BGR2GRAY)

        # Compute SSIM between two images
        (score, diff) = structural_similarity(before_gray, after_gray, full=True)
        # print("Image similarity", score)

        diff = (diff * 255).astype("uint8")
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]

        arr = [cv2.contourArea(i) for i in contours]

        sort_arr = sorted(arr, reverse=True)


        c = contours[arr.index(sort_arr[0])]
        result=self.get_thershold_value(self.rect, cv2.boundingRect(c))
        if result['Area left']<0.90:
            area = cv2.contourArea(c)
            if area > 40:
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(before_croped, (x, y), (x + w, y + h), (36, 255, 12), 2)
                cv2.rectangle(after_cropped, (x, y), (x + w, y + h), (36, 255, 12), 2)
                frame1[self.rect[1]:self.rect[1] + after_cropped.shape[0],
                self.rect[0]:self.rect[0] + after_cropped.shape[1]] = after_cropped
            # self.image_show(before_gray)

            return True, frame1, result['Area left']
        else:
            return False,frame1, result['Area left']



# if __name__=="__main__":
#     image="frame.jpg"
#     arr = np.array([[441, 207],
#                     [792, 142],
#                     [1041, 136],
#                     [1041, 95],
#                     [1447, 126],
#                     [1496, 308],
#                     [1432, 704],
#                     [1099, 725],
#                     [691, 711],
#                     [464, 709],
#                     [467, 440],
#                     [428, 334]],
#                    np.int32)
#     obj=ClutterDetection(crop_cordinates=arr,base_image_path=image)
#     cap = cv2.VideoCapture("/media/parth/7AF0E017F0DFD809/Ubuntu/SAI/WIWO/Clutter_Data/No Interaction/1-6-1.mp4")
#     i = 0
#     while (True):
#         ret, frame = cap.read()
#         if frame is None:
#             break
#         status, frame1 = obj.get_cart_info(frame)
#         if status:#obj.get_cart_info(frame):
#             image = cv2.putText(frame1, 'Cart', (50, 50), cv2.FONT_HERSHEY_SIMPLEX,
#                                 1, (0, 0, 255), 2, cv2.LINE_AA)
#
#         cv2.imshow("after Cropped", frame1)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
#     cap.release()
#     cv2.destroyAllWindows()
