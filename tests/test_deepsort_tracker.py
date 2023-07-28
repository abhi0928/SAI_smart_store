#TODO: Tracker test environment, detections file, mot benchmark
import pytest

from trackers.deepsort_tracker import DeepSort_Tracker

@pytest.fixture()
def tracker():
    tracker = DeepSort_Tracker()
    return tracker

def test_tracker_load(tracker):
    pass