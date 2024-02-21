from flask import Response
import cv2
import numpy as np
import os
import time
import datetime
from flask import Flask, render_template, stream_with_context
from threading import Thread, Lock
from queue import Queue
import localDB

template_dir = os.path.abspath('./')
app = Flask(__name__,template_folder=template_dir)
frames_queue = Queue(maxsize=10)
count = 0
fps = 0
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

@app.route('/history/<dateFROM>/<dateTO>')
def history_route(dateFROM,dateTO):
    return Response(localDB.full_table(dateFROM, dateTO), mimetype='text/csv')
        
@app.route('/count/<date>')
def count_route(date):
    return Response(str(localDB.count_one_day(date)) + "\n", mimetype='text/csv')
