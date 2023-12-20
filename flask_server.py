from flask import Response
import cv2
import numpy as np
import os
import time
from flask import Flask, render_template, stream_with_context
from threading import Thread, Lock
from queue import Queue
import sqlite3

template_dir = os.path.abspath('./')
app = Flask(__name__,template_folder=template_dir)
db = sqlite3.connect("eggs.db", check_same_thread=False)
crt_sql = '''CREATE TABLE IF NOT EXISTS counted (
   datetime NUMERIC,
   count INTEGER
);'''
rows = db.execute(crt_sql)

cursor = db.cursor()

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

def csv_select(dateFROM,dateTO):
    cursor.execute(f"SELECT * FROM counted where datetime > datetime('{dateFROM}') AND datetime < datetime('{dateTO}')")
    result = "Datetime, N\n"
    for row in cursor:
        result = result + f"{row[0]}, {row[1]}\n"
    yield result

def query_csv(date):
    cursor.execute(f"SELECT sum(count) FROM counted where date(datetime) == date('{date}')")
    rows = cursor.fetchall()
    yield str(rows[0][0]) + "\n"

@app.route('/history/<dateFROM>/<dateTO>')
def history_route(dateFROM,dateTO):
    return Response(csv_select(dateFROM, dateTO), mimetype='text/csv')
        
@app.route('/count/<date>')
def count_route(date):
    return Response(query_csv(date), mimetype='text/csv')

def insert(N):
    cursor.execute(f"INSERT INTO counted VALUES(datetime('now', 'localtime'), {N})") 
    db.commit()

    

if __name__ == "__main__":
    from picamera2 import Picamera2
    from libcamera import Transform
    import threading
    import time
    
    def runserver():
        app.run(debug=False, host="0.0.0.0")

    thrServer = threading.Thread(target = runserver)
    thrServer.start()
    
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (320,240)}, transform = Transform(vflip=0,hflip=0)))
    picam2.start()
    while True:
        start = time.time()
        with lock: 
            frame = picam2.capture_array("main")
        if frames_queue.qsize() < 10:
            frames_queue.put_nowait(frame)
        print(f"fps = {(1/(time.time() - start)):.2f}",end='\r')
