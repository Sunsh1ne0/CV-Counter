from fastapi import FastAPI, HTTPException, Path, Depends
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
from queue import Queue
from pydantic import BaseModel, EmailStr
import os
import yaml
import json
import cv2
from typing import Annotated, Optional, Union
import signal

def load_yaml_with_defaults(file_path):
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
        return config
    
templates = Jinja2Templates(directory='templates')
config = load_yaml_with_defaults('config.yaml')
current_sessions = []
frames_queue = Queue(maxsize=1)
pts_queue = Queue(maxsize=1)

def teardown_request_func():
     if stopServer == 1:
        os._exit(0)

app = FastAPI(dependencies=[Depends(teardown_request_func)])

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.absolute() / "static"),
    name="static",
)

@app.route('/', methods = ['GET', 'POST'])
async def index(request: Request):
    if request.client.host not in current_sessions:
        return RedirectResponse("/login")
    return templates.TemplateResponse('./index.html',
                                    context={"request": request,
                                    'FarmId': config['device']['FarmId'], 
                                    'LineId': config['device']['LineId']}
                                )

@app.get('/get_config')
async def get_config(request: Request):
    return JSONResponse(config)

def generate_frames():
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, 30]
            while True:
                # with lock: 
                if frames_queue.qsize() > 0: 
                    frame = frames_queue.get()
                    ret, buffer = cv2.imencode('.jpg', frame, encode_param)
                    yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + bytearray(buffer) + b'\r\n')
                    
@app.get('/stream')
def video_feed(request: Request):
    return StreamingResponse(generate_frames(), media_type='multipart/x-mixed-replace; boundary=frame')


def generate_pts():
    while True:
        if pts_queue.qsize() > 0: 
            states, cords = pts_queue.get()
            msg = {"cords": cords, "states": states}
            json_msg = json.dumps(msg)
            response =  f"data: {json_msg}\n\n" 
            yield response

@app.get('/stream_json')
def stream_json():
    return StreamingResponse(generate_pts(), media_type="text/event-stream")

stopServer = 0
@app.post('/upload_config')
async def upload_file(request: Request):
    global stopServer
    # print(request)
    new_config = await request.json()
    # print(new_config)
    if new_config != None:
        os.system("cp config.yaml config.yaml.bac")
        ### TODO добавить валидацию json
        with open("config.yaml","w") as f:
            yaml.dump(new_config,f)
        stopServer = 1
        return {"success": True, 
                "message": "Server is restarting" }
    return {"success": False, 
            "message": "Server is restarting" }


@app.route('/login', methods=['GET', 'POST'])
async def login(request: Request):
    
    if request.method == 'POST':
        body = await request.body()
        if body == b'':
    #     # устанавливаем сессию для пользователя
            if request.client.host not in current_sessions:
                if not current_sessions:
                    current_sessions.append(request.client.host)
                    return RedirectResponse("/")
                else:
                    return RedirectResponse("/reject")
            return RedirectResponse("/")
        # return RedirectResponse("/")
    return templates.TemplateResponse('./login.html',
                                    context={"request": request})

@app.route('/reject', methods=['GET', 'POST'])
def reject(request: Request):
    return HTMLResponse(
        """
        <p>
        Вы не можете подключиться
        </p>
        """)

@app.post('/disconnect')
def disconnect():
    current_sessions.pop(-1)
    return RedirectResponse("/login")

def run(framesQ, ptsQ):
    global frames_queue
    global pts_queue
    frames_queue = framesQ
    pts_queue = ptsQ
    uvicorn.run('fastapi_server:app', host="0.0.0.0", port=8000)

# if __name__ == "__main__":
#     uvicorn.run('fastapi_server:app', host="127.0.0.1", port=8000, reload=True)
