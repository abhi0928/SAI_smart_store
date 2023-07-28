# Walk in Walk Out - Non Theft

### TODOs
Logging
Docstrings and Comments
Unit testing and testing pyramid
Documenting Terms used in the project

## Installation
##### Clone the Repo 
git clone https://github.com/memona008/WIWO.git

##### Make Virtual environment and activate it
```shell 
python -m venv env
```

##### Install Requirements
```shell 
pip3 install -r requirements.txt 
```

##### Create a config.py file with following constants (It should not be added in git)
All values are added for example. These constant values will vary according to each store


- `SYSTEM_PROXY = "http:\\proxy:80\"`
If the System is using any kind of proxy, add that proxy here
- `OUTPUT_FOLDER_NAME = "Shoppers\" `
It's a path where the cuttings of video will be saved
- `FFMPEG_BIN_PATH_WINDOWS = r"C:\ffmpeg\bin\ffmpeg.exe"`
path where ffmpeg.exe is located
- `EMPTY_STOCK_BOX_SIZE_IN_PERCENT = 0.10`
It is the percentage of box relative to whole frame, which will be considered as empty stock section
- `PARTIALLY_EMPTY_STOCK_BOX_SIZE_IN_PERCENT=[0.03, 0.099]`
It is the range of percentage relative to whole frame, which will be considered as partially empty stock section
- `STORE_ID=5` It is a unique id which is assigned to each store via SAI database
- `CAMERA_TO_AISLE_ID_MAPPING={'1': 320, '2': 456}` It is dict which is mapping each camera number (keys) to their unique id stored in SAI database
- `base_frames={'1': "assets/1.jpg"}` It is the dict of camera (keys) to path where the base frame lies for clutter detection purpose 
- `END_PROCESSING_TIME="20:00:00"` If a script runs on live feed, and we want it to end at particular time, add it here
- `STOCK_CLUTTER_TARGET_AISLES=['1','2,'3']` It's the array containing the camera numbers on which the stock and clutter script will be running in live feed
- `YOLO_WEIGHTS = 'yolov5l'` The Yolo weight we need to use if we are using yolo for detection


#### Create a .env file and have following variables in it (All API endpoints)
```
BASE_LINK = http://test-api-link
STOCK_ROUTE = add_empty_stock
CLUTTER_ROUTE = add_clutter
```

## Getting Started

##### Now you can run the script with following parameters
```shell
python main.py [--source ${SOURCE}] [--destination ${DESTINATION}] \
    [--camera_no ${CAMERA_NO}] \
    [--processing_mode ${PROCESSING_MODE}] \
    [--display_result ${DISP_RES}] [--real_time_interaction ${REAL_TIME_INTERACTION}]
```

The script takes multiple arguments as input
- `--source (required)`: Path of Video or any rtsp link or it can be "0" for webcam.
- `--destination`: Folder in which the results will be saved, it's not required if it's not given, script will automatically create a folder in relative path OUTPUT_FOLDER/{DATE} Live Results/{camera_no}/
- `--api-calls`: `True` or `False` (whether to send notifications to server in livestream or not) 
- `--camera_no (required)`: Camera number of feed/video
- `--processing_mode (required)`: Detection and tracking mode e.g., `yolo`, `openvino`
- `--display_result (required if wants to display)`: `True` Whether to display video with results in separate window
- `--real_time_interaction (required if wants to save videos based on item interaction)`: `True` Will save video with real time interactions with aisle

