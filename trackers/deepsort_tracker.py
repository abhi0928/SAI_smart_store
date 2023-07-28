import torch

import numpy as np

from trackers.deep_sort.deep_sort import DeepSort
from trackers.deep_sort.utils.parser import get_config

from torchvision.ops.boxes import box_convert as torch_box_convert

class DeepSort_Tracker:
    
    def __init__(self) -> None:
        self.tracker = self._initialize_deepsort("deep_sort/configs/deep_sort.yaml")
        
    def _initialize_deepsort(self, config_deepsort):
        cfg = get_config()
        cfg.merge_from_file(config_deepsort)
        deepsort = DeepSort(cfg.DEEPSORT.REID_CKPT,
                            max_dist=cfg.DEEPSORT.MAX_DIST, min_confidence=cfg.DEEPSORT.MIN_CONFIDENCE,
                            nms_max_overlap=cfg.DEEPSORT.NMS_MAX_OVERLAP, max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                            max_age=cfg.DEEPSORT.MAX_AGE, n_init=cfg.DEEPSORT.N_INIT, nn_budget=cfg.DEEPSORT.NN_BUDGET,
                            use_cuda=True)
        return deepsort

    def update(self, preds, img):
        
        outputs = np.empty((0, 5))

        xywhs, confs = [], []
        # Adapt detections to deep sort input format
        for pred in preds:
            
            xyxy = pred[0:4]if type(pred) is torch.Tensor else torch.from_numpy(pred[0:4])
            conf = pred[4]
            
            cxcywh = torch_box_convert(xyxy, 'xyxy', 'cxcywh').numpy()
            xywhs.append(cxcywh)
            confs.append([conf.item()])

        if len(xywhs) > 0:
            with torch.no_grad():
                # Pass detections to deepsort
                outputs = self.tracker.update(torch.Tensor(xywhs), torch.Tensor(confs), img)
                
        return outputs
