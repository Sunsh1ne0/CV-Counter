import cv2
import os
from ultralytics import YOLO
import time
import datetime
from picamera2 import Picamera2
from libcamera import Transform
import threading
import flask_server
from libcamera import controls
from collections import defaultdict 
import numpy as np
import TelemetryServer
import yaml
import localDB

import draw


track_history = defaultdict(lambda: [[], False, 0])
count = 0
count_lock = threading.Lock()

def is_track_pass_board(track, horizontal = False):
    is_left_point_exist = 0
    is_right_point_exist = 0
    left_point_frame = 0
    right_point_frame = 0

    if horizontal:
        index = 1
        criteria = height
    else:
        index = 0
        criteria = width

    for i in range(len(track)):
        point = track[i]
        if (point[index] < int(criteria * enter_zone_part)):
            is_left_point_exist = 1
            left_point_frame = i
        if (point[index] > int(criteria * end_zone_part)):
            is_right_point_exist = 1
            right_point_frame = i

    if (is_left_point_exist * is_right_point_exist == 1 and
            left_point_frame < right_point_frame):
        return True
    return False

def is_track_actual(track):
    if (len(track) < 2):
            return False
    return True

def update_tracks(results, horizontal = False):
    global count
    if(results[0].boxes.id != None):
        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()
        if horizontal:
            index = 1
            criteria = height
        else:
            index = 0
            criteria = width
        for box, track_id in zip(boxes, track_ids):
            x, y, w, h = box
            track_C = track_history[track_id]
            track = track_C[0]
            is_counted = track_C[1]
            track.append((float(x),float(y)))
            if track[-1][index] > criteria * end_zone_part and is_counted == False:
                if is_track_pass_board(track, horizontal = horizontal):
                    with count_lock:
                        count += 1
                    track_C[1] = True
    else:
        track_ids = []

    ## clear lost
    keys = list(track_history.keys())
    for key in keys:
        if not key in track_ids:
            if( track_history[key][2] < 30):
                track_history[key][2] += 1
            else:
                del track_history[key]
            
       
        

def runserver():
    flask_server.app.run(debug=False, host="0.0.0.0")

def saveImg(frame, FarmId, LineId, DateTime):
    folder = f"/home/pi/EggCounter/frames/{FarmId}/{LineId}/{datetime.datetime.today().strftime('%Y-%m-%d')}"
    if not os.path.exists(folder): 
        os.makedirs(folder) 

    strTime = datetime.datetime.fromtimestamp(DateTime).strftime('%H_%M_%S')
    cv2.imwrite(folder + f"/{strTime}.jpg", frame)


def insert_counted_toDB(): 
    global count
    global last_frame
    FarmId = config["device"]["FarmId"]
    LineId = config["device"]["LineId"]
    remoteTelemetry = TelemetryServer.TelemetryServer(host = config["server"]["hostname"],
                                      port = config["server"]["port"],
                                      FarmId = FarmId,
                                      LineId = LineId)
    last_count = 0 
    while True:
        time.sleep(60) 
        with count_lock:
            delta = count - last_count
            last_count = count

        needSaveFrame.clear()
        needSaveFrame.wait()
        datetime = time.time()
        remoteTelemetry.send_count(delta, datetime)
        saveImg(last_frame, FarmId, LineId, datetime)

def main_thread():
    global last_frame
    i = 0
    while True:
        start = time.time()
        frame1 = picam2.capture_array("main")
        width = frame1.shape[1]
        height = frame1.shape[0]

        frame = frame1[:int(height*0.8),:,:]
        width = frame.shape[1]
        height = frame.shape[0]
        horizontal = True

        # Run YOLOv8 tracking on the frame, persisting tracks between frames
        with flask_server.lock: 
            results = model.track(frame, persist=True, imgsz=128, tracker="tracker.yaml",verbose=False)
            update_tracks(results,horizontal = horizontal)
            annotated_frame = draw.tracks(frame, track_history)
            annotated_frame = draw.enter_end_zones(annotated_frame, enter_zone_part, end_zone_part, horizontal = horizontal)
            annotated_frame = draw.count(annotated_frame, count)
            if not needSaveFrame.is_set():
                last_frame = annotated_frame.copy()
                needSaveFrame.set()
            print(f"fps = {(1/(time.time() - start)):.2f} EGGS = {count}",end='\r')

        # Visualize the results on the frame
        if flask_server.frames_queue.qsize() == 0:
            flask_server.frames_queue.put_nowait(annotated_frame.copy())
           
def load_yaml_with_defaults(file_path):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
        return config

if __name__ == "__main__":
    config = load_yaml_with_defaults("config.yaml")
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (320,240)}, 
                                                         transform = Transform(vflip=config["camera"]["vflip"],
                                                                               hflip=config["camera"]["hflip"])))
    picam2.set_controls({"Saturation": 1, 
                         "AeEnable": config["camera"]["AeEnable"],
                         "AnalogueGain": config["camera"]["analogueGain"],
                         "ExposureTime": config["camera"]["ExposureTime"],
                         "AwbEnable": False,
                         "AwbMode": controls.AwbModeEnum.Indoor,
                         "NoiseReductionMode" : controls.draft.NoiseReductionModeEnum.Off,
                         "FrameRate":60})
    picam2.start()
    frame = picam2.capture_array("main")
    width = frame.shape[1]
    height = frame.shape[0]
    last_frame = frame.copy()
    # Load the YOLOv8 model
    model = YOLO(config["model"]["path"])
    enter_zone_part = config["camera"]["enter_zone_part"]
    end_zone_part = config["camera"]["end_zone_part"]

    needSaveFrame = threading.Event()
    saveImgLock = threading.Lock()
    thrServer = threading.Thread(target = runserver)
    thrServer.start()

    thrInsert = threading.Thread(target = insert_counted_toDB)
    thrInsert.start()

    main_thread()
    thrInsert.join()
    thrServer.join()
