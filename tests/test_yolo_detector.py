import pytest
import cv2
import numpy as np
from detectors.yolo_detector import Yolo_Detector


@pytest.fixture()
def detector(config):
    assert 'yolo' in config['detector']
    detector_config = config['detector']['yolo']
    det = Yolo_Detector(**detector_config)
    return det

@pytest.fixture()
def detector_batch(detector, config):
    detector.batch_size = 2
    return detector

def test_detector_load_model(detector, config):
    detector_config = config['detector']['openvino']
    assert isinstance(detector, Yolo_Detector)
    assert detector.batch_size == detector_config['batch_size']
    assert detector.device == detector_config['device']

def test_detector_infer(detector):
    real_image = cv2.imread(r"./tests/test_detector.png")
    preds = detector.infer([real_image])

def test_detector_infer_batch(detector_batch):
    dummy_image = np.random.randint(255,size=(1920,1080,3), dtype=np.uint8)
    real_image = cv2.imread(r"./tests/test_detector.png")
    preds = detector_batch.infer([real_image, dummy_image])

def test_detector_infer_batch_exception(detector_batch):
    dummy_image = np.random.randint(255,size=(1920,1080,3), dtype=np.uint8)

    with pytest.raises(ValueError) as e:
        preds = detector_batch.infer([dummy_image])
    