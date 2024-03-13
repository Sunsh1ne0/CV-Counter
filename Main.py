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
import numpy as np
import TelemetryServer
import yaml
import localDB
import draw
from counter import Counter


       
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
    global count
    i = 0
    horizontal = True

    frame1 = picam2.capture_array("main")
    width = frame1.shape[1]
    height = frame1.shape[0]
        
    frame = frame1[:int(height*0.8),:,:]
    width = frame.shape[1]
    height = frame.shape[0]


    counter = Counter(enter_zone_part, end_zone_part, 
                      horizontal, height, width)


    while True:
        start = time.time()
        frame1 = picam2.capture_array("main")
        width = frame1.shape[1]
        height = frame1.shape[0]
        
        frame = frame1[:int(height*0.8),:,:]
        width = frame.shape[1]
        height = frame.shape[0]

        # Run YOLOv8 tracking on the frame, persisting tracks between frames
        with flask_server.lock: 
            results = model.track(frame, persist=True, imgsz=128, tracker="tracker.yaml", verbose=False)
            dCount = counter.update(results)
            with count_lock:
                count = count + dCount
            annotated_frame = draw.tracks(frame, counter.track_history)
            annotated_frame = draw.enter_end_zones(annotated_frame, enter_zone_part, end_zone_part, horizontal)
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
