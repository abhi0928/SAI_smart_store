
import torch
import cv2
from openvino.inference_engine import IECore, IENetwork

# TODO: Comments and Docs
class OpenVino_Detector:
    """
    OpenVino Person Detector    
    """

    def __init__(self, weights_xml_path, weights_bin_path, batch_size = 1, conf_thres = 0.7, device = "CPU"):

        self.batch_size = batch_size
        self.model_xml = weights_xml_path
        self.model_bin = weights_bin_path
        self.conf_thres = conf_thres
        self.device = device

        self._load_model()
    
    def _load_model(self):
        ie = IECore()
        # net = IENetwork(model=self.model_xml, weights=self.model_bin)
        net = ie.read_network(model=self.model_xml, weights=self.model_bin)
        net.batch_size = self.batch_size
        
        self.net_input_name = next(iter(net.input_info))
        self.net_output_name = next(iter(net.outputs))
        #(batch_size,C,H,W)
        # self.net_input_shape = net.inputs[self.net_input_name].shape
        input_layer = next(iter(net.input_info))
        self.net_input_shape = net.input_info[input_layer].input_data.shape

        self.exec_net = ie.load_network(network=net, num_requests=2, device_name=self.device)

    def _preprocess(self, imgs):
        frames_list = []

        for frame in imgs:
            frame_h, frame_w = frame.shape[:2]
            # Resize image
            in_frame = cv2.resize(frame, (self.net_input_shape[3], self.net_input_shape[2]))
            # Change data layout from HWC to CHW
            in_frame = in_frame.transpose((2, 0, 1))
            # TODO: Verify if we need to reshape now
            # in_frame = in_frame.reshape(self.net_input_shape[1:])
            frames_list.append(in_frame)

        return {self.net_input_name: frames_list}, frame_h, frame_w

    def _postprocess(self, preds, frame_h, frame_w):
        final_preds = [[] for b in range(0,self.batch_size)]
        for obj in preds[0][0]:
            confidence = torch.tensor(obj[2])

            if confidence > self.conf_thres:
                xmin = torch.tensor(int(obj[3] * frame_w))
                ymin = torch.tensor(int(obj[4] * frame_h))
                xmax = torch.tensor(int(obj[5] * frame_w))
                ymax = torch.tensor(int(obj[6] * frame_h))
                if obj[0] < self.batch_size and obj[0] >= 0:
                    final_preds[int(obj[0])].append(torch.tensor([xmin, ymin, xmax, ymax, confidence, 0]).numpy())

        return final_preds

    def infer(self, imgs: list):
        
        if len(imgs) != self.batch_size:
            raise ValueError(f"Expected {self.batch_size} images, received {len(imgs)}")

        input_dict, frame_h, frame_w = self._preprocess(imgs)
        
        cur_request_id = 0
        preds = [[]]
        # TODO: Check if we need this `start_async` instead of `infer` as we 
        # are waiting for async call anyway with `wait(-1)`
        # check https://docs.openvino.ai/2019_R3/classie__api_1_1ExecutableNetwork.html
        # and https://docs.openvino.ai/2019_R3.1/classie__api_1_1InferRequest.html
        self.exec_net.start_async(request_id=cur_request_id, inputs=input_dict)
        if self.exec_net.requests[cur_request_id].wait(-1) == 0:
            preds = self.exec_net.requests[cur_request_id].output_blobs[self.net_output_name]
            preds = preds.buffer

        
        preds = self._postprocess(preds, frame_h, frame_w)
        
        return preds
