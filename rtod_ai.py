from flask import Flask, render_template, Response
import cv2
import os
from imageai.Detection import ObjectDetection
import time
import datetime
from tgbot import send_telegram_alert

app = Flask(__name__)

# Object Detection Setup
detector = ObjectDetection()
detector.setModelTypeAsYOLOv3()
detector.setModelPath(os.path.join("models", "yolov3.pt"))
detector.loadModel()

video_capture = cv2.VideoCapture(0)
frame_rate = 1/2
custom = detector.CustomObjects(person=True, handbag=True, bottle=True)

def generate_frames():
    count = 0
    while True:
        success, frame = video_capture.read()
        if not success:
            break

        detections = detector.detectObjectsFromImage(custom_objects=custom, input_image=frame,
                                                     minimum_percentage_probability=30)

        for detection in detections:
            name = detection["name"]
            percentage_probability = detection["percentage_probability"]
            bounding_box = detection["box_points"]

            cv2.rectangle(frame, (bounding_box[0], bounding_box[1]), (bounding_box[2], bounding_box[3]), (255, 0, 0), 2)
            cv2.putText(frame, f"{name}: {percentage_probability:.2f}%", (bounding_box[0], bounding_box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            if name == "person":
                count += 1
            else:
                count = 0

            if count >= 4:
                last_frame = frame.copy()
                cv2.imwrite("static/last_captured_image.jpg", last_frame)
                count = 0

            if count == 0 and os.path.exists("static/last_captured_image.jpg"):
                bots = [
                    ("7244222902:AAHAsvYUbyIKzr2qjbn2ubRJ40vaN9WVYEE", "5663487142"),
                    ("7371007601:AAGH53hQAmMmmOHXZz9JE5n6JvuXRQ4tRnQ", "1684588431")
                ]
                for bot_token, chat_id in bots:
                    send_telegram_alert(bot_token, chat_id, "static/last_captured_image.jpg",
                                        caption=f"Suspicious activity detected! ({datetime.datetime.now():%Y-%m-%d %H:%M:%S})")
                os.remove("static/last_captured_image.jpg")

        # Encoding frame as jpg
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the frame to the HTML
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
