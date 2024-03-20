from flask import Response, request
import cv2
import numpy as np
import os
import time
import datetime
from flask import Flask, render_template, stream_with_context
from threading import Thread, Lock
from queue import Queue
import localDB
import yaml
import json
import sys
from werkzeug.serving import run_simple




def load_yaml_with_defaults(file_path):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
        return config

template_dir = os.path.abspath('./')
app = Flask(__name__,template_folder=template_dir)
frames_queue = Queue(maxsize=1)
pts_queue = Queue(maxsize=1)
count = 0
fps = 0
lock = Lock()
config = load_yaml_with_defaults('config.yaml')

@app.route('/')
def index():
    return render_template('./index.html', 
                            FarmId=config['device']['FarmId'], 
                            LineId=config['device']['LineId']
                            )

@app.route('/get_config')
def get_config():
    return Response(json.dumps(config), mimetype='application/json')

from flask import jsonify
import json, os, signal



stopServer = 0
@app.route('/upload_config', methods=['POST'])
def upload_file():
    global stopServer
    new_config = request.get_json()
    os.system("cp config.yaml config.yaml.bac")
    ### TODO добавить валидацию json
    with open("config.yaml","w") as f:
        yaml.dump(new_config,f)
    stopServer = 1
    return jsonify({ "success": True, "message": "Server is restarting" })

@app.teardown_request
def teardown_request_func(error=None):
     if stopServer == 1:
        os.kill(os.getpid(), signal.SIGINT)


def generate_frames():
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
            while True:
                with lock: 
                    if frames_queue.qsize() > 0: 
                        frame = frames_queue.get()
                        ret, buffer = cv2.imencode('.jpg', frame, encode_param)
                        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + bytearray(buffer) + b'\r\n')
                    
@app.route('/stream')
def video_feed():
    return Response(stream_with_context(generate_frames()), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_pts():
    while True:
        with lock: 
            if pts_queue.qsize() > 0: 
                states, cords = pts_queue.get()
                msg = {"cords": cords, "states": states}
                json_msg = json.dumps(msg)
                response =  f"data: {json_msg}\n\n" 
                yield response

@app.route('/stream_json')
def stream_json():
    return Response(generate_pts(), mimetype="text/event-stream")
@app.route('/2')
def second_index():
    return render_template('./stream.html',
                            FarmId=config['device']['FarmId'], 
                            LineId=config['device']['LineId'])
    
@app.route('/history/<dateFROM>/<dateTO>')
def history_route(dateFROM,dateTO):
    return Response(localDB.full_table(dateFROM, dateTO), mimetype='text/csv')
        
@app.route('/count/<date>')
def count_route(date):
    return Response(str(localDB.count_one_day(date)) + "\n", mimetype='text/csv')

def run():
    app.run('0.0.0.0',5000)
