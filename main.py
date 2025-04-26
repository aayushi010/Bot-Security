from flask import Flask, render_template, Response
from imageai.Detection import ObjectDetection
import os
import cv2
import time
import datetime
from tgbot import send_telegram_alert

app = Flask(__name__)

# Initialize detector
detector = ObjectDetection()
detector.setModelTypeAsYOLOv3()
detector.setModelPath(os.path.join("models", "yolov3.pt"))
detector.loadModel()

# Start video capture
video_capture = cv2.VideoCapture(0)
frame_rate = 1/2  # Frame rate
custom = detector.CustomObjects(person=True, handbag=True, bottle=True)

count = 0  # To track person detection

def generate_frames():
    global count
    while True:
        success, frame = video_capture.read()
        if not success:
            break

        # Save frame temporarily
        temp_image_path = "temp_frame.jpg"
        cv2.imwrite(temp_image_path, frame)

        # Detect objects
        detections = detector.detectObjectsFromImage(
            custom_objects=custom,
            input_image=temp_image_path,
            output_image_path="temp_detected.jpg",
            minimum_percentage_probability=30
        )

        detected_frame = cv2.imread("temp_detected.jpg")
        frame = detected_frame

        for detection in detections:
            name = detection["name"]
            percentage_probability = detection["percentage_probability"]
            bounding_box = detection["box_points"]

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

        # Clean up temp
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        if os.path.exists("temp_detected.jpg"):
            os.remove("temp_detected.jpg")

        # Encode for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Stream frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)
