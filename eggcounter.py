import cv2
import os
from ultralytics import YOLO
import time
import datetime
from picamera2 import Picamera2
from libcamera import Transform
import threading
from multiprocessing import Process, Queue
import flask_server
from libcamera import controls
import TelemetryServer
import yaml
from draw import Draw
from counter import Counter
       
def runserver(QueueF, QueueP):
    flask_server.run(QueueF, QueueP)

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
        time.sleep(20) 
        with count_lock:
            delta = count - last_count
            last_count = count

        needSaveFrame.clear()
        needSaveFrame.wait()
        datetime = time.time()
        remoteTelemetry.send_count(delta, datetime)
        saveImg(last_frame, FarmId, LineId, datetime)

def crop(frame):
    crop_x0, crop_x1, crop_y0,crop_y1 = config["camera"]["crop"]
    h = frame.shape[0]
    w = frame.shape[1]
    x0 = int(crop_x0 * w)
    x1 = int(crop_x1 * w)
    y0 = int(crop_y0 * h)
    y1 = int(crop_y1 * h)
    out = frame[y0:y1,x0:x1,:]
    return out


def main_thread():
    global last_frame
    global count
    frame_number = 0

    frame = picam2.capture_array("main")
    frame = crop(frame)
    width = frame.shape[1]
    height = frame.shape[0]
    counter = Counter(enter_zone_part, end_zone_part, 
                      horizontal, height, width)
    
    draw = Draw(resolution, enter_zone_part, end_zone_part, horizontal)
    
    while True:
        if procServer.is_alive() == False:
            os._exit(0)
        start = time.time()
        frame = picam2.capture_array("main")
        frame = crop(frame)
        width = frame.shape[1]
        height = frame.shape[0]
        
        # Run YOLOv8 tracking on the frame, persisting tracks between frames
        results = model.track(frame, persist=True, imgsz=128, tracker="tracker.yaml", verbose=False)

        dCount = counter.update(results, frame_number)
        with count_lock:
            count = count + dCount

        annotated_frame = draw.process(frame, counter.eggs, count)
        frame_number += 1
        
        if not needSaveFrame.is_set():
            last_frame = frame.copy()
            needSaveFrame.set()
        print(f"fps = {(1/(time.time() - start)):.2f} EGGS = {count}",end='\r')
        
        # Visualize the results on the frame
        if qFrames.qsize() == 0:
            qFrames.put_nowait(annotated_frame.copy())
            
        if qPoints.qsize() == 0:
            qPoints.put_nowait(list(counter.last_new()))
        

def load_yaml_with_defaults(file_path):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
        return config

if __name__ == "__main__":
    os.system('pinctrl FAN_PWM op dl')
    config = load_yaml_with_defaults("config.yaml")
    
    # Getting data from config.yaml
    horizontal = config["camera"]['horizontal']
    enter_zone_part = config["camera"]["enter_zone_part"]
    end_zone_part = config["camera"]["end_zone_part"]
    resolution = config["camera"]["resolution"]

    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": resolution}, 
                                                         transform = Transform(vflip=config["camera"]["vflip"],
                                                                               hflip=config["camera"]["hflip"])))
    picam2.set_controls({"Saturation": 1, 
                         "AeEnable": config["camera"]["AeEnable"],
                         "AnalogueGain": config["camera"]["analogueGain"],
                         "ExposureTime": config["camera"]["ExposureTime"],
                         "AwbEnable": False,
                         "AwbMode": controls.AwbModeEnum.Indoor,
                         "NoiseReductionMode" : controls.draft.NoiseReductionModeEnum.Off,
                         "FrameRate": config["camera"]["fps"]})
    picam2.start()
    frame = picam2.capture_array("main")

    frame = crop(frame)
    width = frame.shape[1]
    height = frame.shape[0]
    last_frame = frame.copy()
    count = 0
    # Load the YOLOv8 model
    model = YOLO('./models/model.tflite')


    needSaveFrame = threading.Event()
    event = threading.Event()
    count_lock = threading.Lock()
    thrInsert = threading.Thread(target = insert_counted_toDB,daemon=True)

    qFrames = Queue(maxsize=1)
    qPoints = Queue(maxsize=1)

    procServer = Process(target = runserver, args = (qFrames, qPoints), daemon=True)
    
    # thrServer.start()    
    procServer.start()
    thrInsert.start()

    main_thread()
