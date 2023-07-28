import torch
import numpy as np

class Yolo_Detector:
    CLASSES = [0]  # class 0 is person
    IMG_SIZE = 480

    def __init__(self, weights, checkpoint_path=None, batch_size = 1, conf_thres = 0.5, iou_thres = 0.3, device = "CPU"):
        if checkpoint_path is None:
            self.model = torch.hub.load('ultralytics/yolov5', weights)
        else:
            self.model = torch.hub.load('ultralytics/yolov5', weights, path=checkpoint_path)

        self.model.iou = iou_thres
        self.model.conf = conf_thres
        self.model.classes = self.CLASSES
        self.batch_size = batch_size
        self.device = device

        if device == "GPU" and not torch.cuda.is_available():
            raise ValueError("GPU is not available on this machine.")
        if device == "CPU":
            self.model = self.model.cpu()

    def infer(self, imgs: list):
        
        if len(imgs) != self.batch_size:
            raise ValueError(f"Expected {self.batch_size} images, received {len(imgs)}")
        
        with torch.no_grad():
            preds = self.model(imgs, size=self.IMG_SIZE)
        # TODO: Test with GPU device, preds needs to be on cpu before returning
        return preds.xyxy
        