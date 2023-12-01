from flask import Response
import cv2
import numpy as np
import os
import time
from flask import Flask, render_template, stream_with_context
from threading import Thread, Lock
from queue import Queue

template_dir = os.path.abspath('./')
app = Flask(__name__,template_folder=template_dir)

frames_queue = Queue(maxsize=100)
lock = Lock()

@app.route('/')
def index():
    return render_template('./index.html')


def generate_frames():
            while True:
                with lock: 
                    if frames_queue.qsize() > 0: 
                        frame = frames_queue.get()
                        ret, buffer = cv2.imencode('.jpg', frame)
                        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + bytearray(buffer) + b'\r\n')
@app.route('/output')


def video_feed():
    return Response(stream_with_context(generate_frames()), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    from picamera2 import Picamera2
    from libcamera import Transform
    import threading
    
    def runserver():
        app.run(debug=False, host="0.0.0.0")

    thrServer = threading.Thread(target = runserver)
    thrServer.start()
    
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (320,240)}, transform = Transform(vflip=0,hflip=0)))
    picam2.start()
    while True:
        frame = picam2.capture_array("main")
