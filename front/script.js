const img = new Image();
let frameCount = 0;

let resolutions =  {"640 x 480 p60":  {"x": 640, "y": 480, 'fps': 60},
                    "640 x 480 p90":  {"x": 640, "y": 480, 'fps': 90},
                    "1296 x 972 p42": {"x": 1296, "y": 972, 'fps': 42},
                    "2592 x 1944 p15": {"x": 2592, "y": 1944, 'fps': 15}};

function handleNewFrame() {
    frameCount++;
    console.log("Новый кадр получен");
    document.getElementById('frame').appendChild(img);
}

let resolution = [640, 480];

function drawPoints(coords, states) {
    const container = document.getElementById('frame');
    let pts_old = document.getElementsByClassName('point');
    while (pts_old[0]) {
        pts_old[0].parentNode.removeChild(pts_old[0]);
    }

    const scaleFactorX = container.offsetWidth / resolution[0];
    const scaleFactorY = container.offsetHeight / resolution[1];

    coords.forEach((coord, index) => {
        const point = document.createElement('div');
        point.classList.add('point');
        point.style.left = (coord[0] * scaleFactorX) + 'px';
        point.style.top = (coord[1] * scaleFactorY) + 'px';
        point.style.backgroundColor = states[index] == 1 ? 'green' : 'red';
        container.appendChild(point);
    });
}

img.onload = handleNewFrame;
img.src = "/stream";

const eventsource = new EventSource("/stream_json");
eventsource.onmessage = function (event) {
    let msg = JSON.parse(event.data);
    drawPoints(msg.cords, msg.states);
}

function toggleSettings() {
    let serverSettings = document.getElementById('serverSettings');
    let cameraSettings = document.getElementById('cameraSettings');
    serverSettings.classList.toggle('show');
    cameraSettings.classList.toggle('show');
}

function getConfig() {
    fetch('/get_config')
        .then(response => response.json())
        .then(data => {
            document.getElementById('FarmId').value = data.device.FarmId;
            document.getElementById('LineId').value = data.device.LineId;
            document.getElementById('Host').value = data.server.hostname;
            document.getElementById('Port').value = data.server.port;
            document.getElementById('analogueGain').value = data.camera.analogueGain;
            document.getElementById('analogueGainValue').textContent = data.camera.analogueGain;
            document.getElementById('ExposureTime').value = data.camera.ExposureTime;
            document.getElementById('exposureTimeValue').textContent = data.camera.ExposureTime;
            document.getElementById('AeEnable').checked = data.camera.AeEnable;
            document.getElementById('vflip').checked = data.camera.vflip;
            document.getElementById('hflip').checked = data.camera.hflip;
            document.getElementById('enter_zone_part').value = data.camera.enter_zone_part;
            document.getElementById('end_zone_part').value = data.camera.end_zone_part;
            document.getElementById('horizontal').checked = data.camera.horizontal;
            resolution = data.camera.resolution;
            const fps  = data.camera.fps;

            document.getElementById('resolution').value = String(resolution[0]) + ' x ' +  String(resolution[1]) + ' p' + String(fps);

            const cropLeftValue = parseFloat(data.camera.crop[0]);
            const cropRightValue = parseFloat(data.camera.crop[1]);
            const cropTopValue = parseFloat(data.camera.crop[2]);
            const cropBottomValue = parseFloat(data.camera.crop[3]);

            cropValues[0] = cropLeftValue;
            cropValues[1] = cropRightValue;
            cropValues[2] = cropTopValue;
            cropValues[3] = cropBottomValue;

            cropLeftInput.value = cropLeftValue.toFixed(2);
            cropRightInput.value = cropRightValue.toFixed(2);
            cropTopInput.value = cropTopValue.toFixed(2);
            cropBottomInput.value = cropBottomValue.toFixed(2);

            updateCropInputValues();

            document.getElementById('enter_zone_part').value = data.camera.enter_zone_part;
            document.getElementById('end_zone_part').value = data.camera.end_zone_part;
            updateEnterZonePartValue();
            updateEndZonePartValue();
        })
        .catch(error => {
            console.error('Ошибка при загрузке конфигурации:', error);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    toggleSettings();
    getConfig();
  });
document.querySelector('.settingsButton').addEventListener('click', getConfig);

function applySettings() {
    const FarmId = document.getElementById('FarmId').value.trim();
    const LineId = document.getElementById('LineId').value.trim();
    const Host = document.getElementById('Host').value.trim();
    const Port = document.getElementById('Port').value.trim();
    const analogueGain = document.getElementById('analogueGain').value.trim();
    const ExposureTime = document.getElementById('ExposureTime').value.trim();
    const vflip = document.getElementById('vflip').checked;
    const hflip = document.getElementById('hflip').checked;
    const AeEnable = document.getElementById('AeEnable').checked;
    const enter_zone_part = document.getElementById('enter_zone_part').value.trim();
    const end_zone_part = document.getElementById('end_zone_part').value.trim();
    const horizontal = document.getElementById('horizontal').checked;
    const crop = collectCropData();
    const resolution_key = document.getElementById('resolution').value.trim();

    resolution = [resolutions[resolution_key]['x'], resolutions[resolution_key]['y']];
    const fps = resolutions[resolution_key]['fps'];

    if (FarmId === '' || LineId === '' || Host === '' || Port === '' || analogueGain === '' || ExposureTime === '' || enter_zone_part === '' || end_zone_part === '' || horizontal === '' || !crop) {
        alert('Пожалуйста, заполните все поля');
        return;
    }

    if (isNaN(LineId) || isNaN(Port) || isNaN(analogueGain) || isNaN(ExposureTime) || isNaN(enter_zone_part) || isNaN(end_zone_part)) {
        alert('Пожалуйста, убедитесь, что числовые поля содержат числовые значения');
        return;
    }

    const updatedConfig = {
        camera: {
            AeEnable: AeEnable,
            ExposureTime: parseInt(ExposureTime),
            analogueGain: parseInt(analogueGain),
            crop: crop,
            end_zone_part: parseFloat(end_zone_part),
            enter_zone_part: parseFloat(enter_zone_part),
            hflip: hflip,
            horizontal: horizontal,
            vflip: vflip,
            resolution: resolution,
            fps: parseInt(fps)
        },
        device: {
            FarmId: FarmId,
            LineId: parseInt(LineId)
        },
        server: {
            hostname: Host,
            port: Port
        }
    };

    const jsonData = JSON.stringify(updatedConfig);

    fetch('/upload_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: jsonData
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка при отправке запроса');
            }
            console.log('Настройки сохранены успешно');
        })
        .catch(error => {
            console.error('Ошибка при отправке запроса:', error);
        });
    setTimeout(function () {
        window.location.reload(true);
    }, 1000);
}

function collectCropData() {
    const cropValues = [
        parseFloat(document.getElementById('cropLeft').value.trim()),
        parseFloat(document.getElementById('cropRight').value.trim()),
        parseFloat(document.getElementById('cropTop').value.trim()),
        parseFloat(document.getElementById('cropBottom').value.trim())
    ];

    if (cropValues.some(isNaN)) {
        alert('Пожалуйста, убедитесь, что значения обрезки являются числами');
        return null;
    }

    return cropValues;
}


document.getElementById('saveSettingsButton').addEventListener('click', applySettings);

function updateDateTime() {
    const currentDate = new Date();
    const options = { weekday: 'short', year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric' };
    const formattedDate = currentDate.toLocaleString('ru-RU', options).replace(' в ', ' ');
    document.getElementById('currentDateTime').textContent = formattedDate;
}

updateDateTime();
setInterval(updateDateTime, 1000);

function analogueGainValue(value) {
    const analogueGainValueSpan = document.getElementById('analogueGainValue');
    analogueGainValueSpan.textContent = value;
}

function exposureTimeValue(value) {
    const exposureTimeValueSpan = document.getElementById('exposureTimeValue');
    exposureTimeValueSpan.textContent = value;
}

const enterZonePartInput = document.getElementById('enter_zone_part');
const endZonePartInput = document.getElementById('end_zone_part');

enterZonePartInput.addEventListener('input', function () {
    const enterZonePartValue = parseFloat(enterZonePartInput.value);
    const endZonePartValue = parseFloat(endZonePartInput.value);
    if (enterZonePartValue >= endZonePartValue) {
        endZonePartInput.value = enterZonePartValue + 0.01;
        updateEndZonePartValue();
    }
    updateEnterZonePartValue();
});

endZonePartInput.addEventListener('input', function () {
    const endZonePartValue = parseFloat(endZonePartInput.value);
    const enterZonePartValue = parseFloat(enterZonePartInput.value);
    if (endZonePartValue <= enterZonePartValue) {
        enterZonePartInput.value = endZonePartValue - 0.01;
        updateEnterZonePartValue();
    }
    updateEndZonePartValue();
});

function updateEnterZonePartValue() {
    const enterZonePartValue = parseFloat(enterZonePartInput.value);
    document.getElementById('enter_zone_part_value').textContent = enterZonePartValue.toFixed(2);
}

function updateEndZonePartValue() {
    const endZonePartValue = parseFloat(endZonePartInput.value);
    document.getElementById('end_zone_part_value').textContent = endZonePartValue.toFixed(2);
}

updateEnterZonePartValue();
updateEndZonePartValue();

const cropLeftInput = document.getElementById('cropLeft');
const cropRightInput = document.getElementById('cropRight');
const cropTopInput = document.getElementById('cropTop');
const cropBottomInput = document.getElementById('cropBottom');

const cropInputs = [cropLeftInput, cropRightInput, cropTopInput, cropBottomInput];
const cropValues = [0, 0, 0, 0];

cropInputs.forEach((input, index) => {
    input.addEventListener('input', function () {
        cropValues[index] = parseFloat(this.value);
        updateCropInputValues();
    });
});

function updateCropInputValues() {
    const cropLeftValue = cropValues[0];
    const cropRightValue = cropValues[1];
    const cropTopValue = cropValues[2];
    const cropBottomValue = cropValues[3];

    document.getElementById('cropLeftValue').textContent = cropLeftValue.toFixed(2);
    document.getElementById('cropRightValue').textContent = cropRightValue.toFixed(2);
    document.getElementById('cropTopValue').textContent = cropTopValue.toFixed(2);
    document.getElementById('cropBottomValue').textContent = cropBottomValue.toFixed(2);
}

updateCropInputValues();

function disconnect() {
    const jsonData = JSON.stringify('Disconnect');

    fetch('/disconnect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: jsonData
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка при отключении');
            }
            console.log('Успешно разъединено');
        })
        .catch(error => {
            console.error('Ошибка при отключении:', error);
        });
    // setTimeout(function () {
    //     window.location.reload(true);
    // }, 1000);
}