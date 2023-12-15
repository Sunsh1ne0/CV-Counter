import cv2
from ultralytics import YOLO
import time
from picamera2 import Picamera2
from libcamera import Transform
import threading
import flask_server
from libcamera import controls
from collections import defaultdict 
import numpy as np

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (320,240)}, transform = Transform(vflip=0,hflip=0)))
picam2.set_controls({"Saturation": 1, 
                     "AeEnable": False,
                     "AnalogueGain": 1,
                     "ExposureTime": 50000,
                     "AwbEnable": False,
                     "AwbMode": controls.AwbModeEnum.Indoor,
                     "NoiseReductionMode" : controls.draft.NoiseReductionModeEnum.Off})
picam2.start()

# Load the YOLOv8 model
model = YOLO("/home/pi/EggCounter/models/eggs_YOLOv8n_128_11_12_2023.tflite")
#model = YOLO("/home/pi/EggCounter/best_int8.tflite")

# Open the video file

    
enter_zone_part = 0.65
end_zone_part = 0.75

def draw_enter_end_zones(cv_image,horizontal=False):
        if horizontal:
            cv_image = cv2.line(cv_image, (0, int(height*enter_zone_part)), (width, int(height*enter_zone_part)), (0,0,255), 1)
            cv_image = cv2.line(cv_image, (0, int(height*end_zone_part)), (width, int(height*end_zone_part)), (0,0,255), 1)
        else:
            cv_image = cv2.line(cv_image, (int(width*enter_zone_part),0), (int(width*enter_zone_part),height), (0,0,255), 1)
            cv_image = cv2.line(cv_image, (int(width*end_zone_part), 0), (int(width*end_zone_part), height), (0,0,255), 1)
        return cv_image

track_history = defaultdict(lambda: [[], False])
count = 0

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
    if(results[0].boxes.id == None):
        return
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
        track.append((float(x), float(y)))  # x, y center point
        if track[-1][index] > criteria * end_zone_part and is_counted == False:
            if is_track_pass_board(track, horizontal = horizontal):
                count += 1
                del track_history[track_id]

def draw_count(cv_image):
    return cv2.putText(cv_image, f"{count}", (30,30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 
                       2, cv2.LINE_AA)

def runserver():
    flask_server.app.run(debug=False, host="0.0.0.0")


def insert_counted_toDB(): 
    global count
    last_count = 0
    while True:
        time.sleep(60) 
        flask_server.insert(count - last_count)
        last_count = count

thrServer = threading.Thread(target = runserver)
thrServer.start()

thrInsert = threading.Thread(target = insert_counted_toDB)
thrInsert.start()

#cap = cv2.VideoCapture("/home/pi/Videos/29-09-2023_11h35m44.avi")
i = 0

while True:
    start = time.time()
    # Read a frame from the video
    #success, frame = cap.read()
    frame = picam2.capture_array("main")
    width = frame.shape[1]
    height = frame.shape[0]
    horizontal = True
    success = True
    if success:
        # Run YOLOv8 tracking on the frame, persisting tracks between frames
        with flask_server.lock: 
            results = model.track(frame, persist=True, imgsz=128, tracker="tracker.yaml",verbose=False)
            update_tracks(results,horizontal = horizontal)
            annotated_frame = results[0].plot(labels=False)
            annotated_frame = draw_enter_end_zones(annotated_frame, horizontal = horizontal)
            annotated_frame = draw_count(annotated_frame)

        # Visualize the results on the frame
        if flask_server.frames_queue.qsize() < 10:
            flask_server.frames_queue.put_nowait(annotated_frame.copy())

       
    print(f"fps = {(1/(time.time() - start)):.2f} EGGS = {count}",end='\r')

# Release the video capture object and close the display window
thrServer.join()
thrInsert.join()
cap.release()
cv2.destroyAllWindows()

