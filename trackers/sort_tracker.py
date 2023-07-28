import numpy as np
import torch

from trackers.SORT import Sort


class Sort_Tracker:

    def __init__(self, max_age=1, min_hits=3, iou_threshold=0.3) -> None:
        self.tracker = Sort(max_age=max_age, min_hits=min_hits, iou_threshold=iou_threshold)

    def update(self, preds, img):
        if type(preds) is torch.Tensor:
            preds = preds.cpu().numpy()
        else:
            preds = np.array(preds)
            
        xyxys = np.reshape(preds,(-1, 6))
        
        outputs = self.tracker.update(xyxys[:,:5])

        return outputs.astype(np.int32)

