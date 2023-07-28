import pytest

import numpy as np
import cv2
from detectors.openvino_detector import OpenVino_Detector


@pytest.fixture()
def detector(config):
    assert 'openvino' in config['detector']
    detector_config = config['detector']['openvino']
    det = OpenVino_Detector(**detector_config)
    return det

@pytest.fixture()
def detector_batch(config):
    detector_config = {
        'weights_xml_path': config['detector']['openvino']['weights_xml_path'],
        'weights_bin_path': config['detector']['openvino']['weights_bin_path'],
        'batch_size': 2,
        'conf_thres': 0.7,
        'device': 'CPU'
    }
    det = OpenVino_Detector(**detector_config)
    return det

def test_detector_load_model(detector, config):
    detector_config = config['detector']['openvino']
    assert isinstance(detector, OpenVino_Detector)
    assert detector.batch_size == detector_config['batch_size']
    assert detector.conf_thres == detector_config['conf_thres']
    assert detector.device == detector_config['device']

def test_detector_infer(detector):
    real_image = cv2.imread(r"./tests/test_detector.png")
    preds = detector.infer([real_image])
    
def test_detector_batch_infer(detector_batch):
    dummy_image = np.random.randint(255,size=(1920,1080,3), dtype=np.uint8)
    real_image = cv2.imread(r"./tests/test_detector.png")
    preds = detector_batch.infer([real_image,dummy_image])

    assert len(preds) == 2 

def test_detector_batch_infer_exception(detector_batch):
    dummy_image = np.random.randint(255,size=(1920,1080,3), dtype=np.uint8)

    with pytest.raises(ValueError) as e:
        preds = detector_batch.infer([dummy_image])
    