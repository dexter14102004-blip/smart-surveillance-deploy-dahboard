from ultralytics import YOLO
import cv2
import os

model = YOLO("yolov8n.pt")

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)

    output_path = "static/uploads/output.mp4"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (
        int(cap.get(3)), int(cap.get(4))
    ))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)

        annotated = results[0].plot()
        out.write(annotated)

    cap.release()
    out.release()

    return output_path