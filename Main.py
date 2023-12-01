import cv2
from ultralytics import YOLO
import time
from picamera2 import Picamera2
from libcamera import Transform
import threading
import flask_server

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (320,240)}, transform = Transform(vflip=0,hflip=0)))
picam2.start()

# Load the YOLOv8 model
model = YOLO("./models/best/best_int8.tflite")

# Open the video file
cap = cv2.VideoCapture("/home/pi/Videos/29-09-2023_11h35m44.avi")
video_path = ""

    
def runserver():
    flask_server.app.run(debug=False, host="0.0.0.0")
thrServer = threading.Thread(target = runserver)
thrServer.start()

i = 0
while True:
    start = time.time()
    # Read a frame from the video
    #success, frame = cap.read()
    frame = picam2.capture_array("main")
    success = True
    if success:
        # Run YOLOv8 tracking on the frame, persisting tracks between frames
        with flask_server.lock: 
            results = model.track(frame, persist=True,imgsz=128, tracker="tracker.yaml")
        # Visualize the results on the frame
            annotated_frame = results[0].plot()

#        cv2.imshow("output", annotated_frame)
#        cv2.waitKey(1)
        # Display the annotated frame
        # Break the loop if 'q' is pressed
        if flask_server.frames_queue.qsize() < 100:
            flask_server.frames_queue.put_nowait(annotated_frame.copy())

    print(f"fps = {(1/(time.time() - start)):.2f}")

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()
