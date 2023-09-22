from flask import Flask, render_template_string, request, make_response
import cv2
import numpy as np
import datetime

app = Flask(__name__)
@app.route('/')
def index():
    return render_template_string('''<!DOCTYPE html>
<html>
<head>
    <title>Webcam Recorder</title>
</head>
<body>
    <label for="fps">FPS:</label>
    <input type="number" id="fps" min="1" max="60" value="30">
    <label for="width">Width:</label>
    <input type="number" id="width" min="1" value="640">
    <label for="height">Height:</label>
    <input type="number" id="height" min="1" value="480">
    <label for="cameraSelect">Select Camera:</label>
    <select id="cameraSelect"></select>
    <button id="startButton">Start Recording</button>
    <video id="video" autoplay muted></video>
    <button id="stopButton">Stop Recording</button>
    <video id="outputVideo" controls></video>
    <script>
        document.addEventListener('DOMContentLoaded', async (event) => {
            const video = document.getElementById('video');
            const startButton = document.getElementById('startButton');
            const stopButton = document.getElementById('stopButton');
            const fpsInput = document.getElementById('fps');
            const widthInput = document.getElementById('width');
            const heightInput = document.getElementById('height');
            const cameraSelect = document.getElementById('cameraSelect');
            const outputVideo = document.getElementById('outputVideo');
            let mediaRecorder;
            let mediaStream;
            let chunks = [];

            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');

            videoDevices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `Camera ${cameraSelect.length + 1}`;
                cameraSelect.appendChild(option);
            });

            startButton.addEventListener('click', async () => {
                const selectedCameraId = cameraSelect.value;
                const constraints = {
                    video: {
                        width: { exact: parseInt(widthInput.value) },
                        height: { exact: parseInt(heightInput.value) },
                        deviceId: { exact: selectedCameraId }
                    }
                };

                mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
                const tracks = mediaStream.getVideoTracks();

                if (tracks.length > 0) {
                    const settings = tracks[0].getSettings();
                    constraints.video.frameRate = { ideal: settings.frameRate.max };
                }

                video.srcObject = mediaStream;
                mediaRecorder = new MediaRecorder(mediaStream);

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        chunks.push(event.data);
                    }
                }

                mediaRecorder.onstop = async () => {
                    const combinedBlob = new Blob(chunks, { type: 'video/webm' });
                    const url = URL.createObjectURL(combinedBlob);
                    outputVideo.src = url;

                    const formData = new FormData();
                    formData.append('video', combinedBlob);

                    try {
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.text();
                        console.log(result);
                    } catch (error) {
                        console.error('Error uploading video:', error);
                    }
                }

                mediaRecorder.start();
            });

            stopButton.addEventListener('click', () => {
                mediaRecorder.stop();
                mediaStream.getTracks().forEach(track => track.stop());
            });
        });
    </script>
</body>
</html>
''')




@app.route('/upload', methods=['POST'])
def upload_video():
    uploaded_file = request.files['video']
    cv2.VideoCapture(cv2.CAP_ANY)
    uploaded_file.save(datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.avi')  # Save the file to disk or process it further
    return 'Video uploaded successfully!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
