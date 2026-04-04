import cv2
import csv
import os
import time
import pygame
import requests
import threading
from ultralytics import YOLO
from datetime import datetime


class ObjectDetector:
    def __init__(self, source=0, conf=0.45):
        self.model = YOLO("yolov8n.pt")

        self.source = source
        self.conf = conf
        self.cap = None
        self.running = False
        self.current_frame = None

        # ===== LOGGING =====
        self.log_file = "detection_log.csv"
        self.last_log = 0
        self.log_interval = 10
        self.detections = []

        # ===== ALARM =====
        self.alarm_enabled = True
        self.last_alarm = 0
        self.alarm_interval = 1
        self.human_alarm = "sounds/alarm_human_.wav"
        self.animal_alarm = "sounds/alarm_animal.wav"

        # ===== TELEGRAM =====
        self.bot_token = "8500974327:AAEYXxhngYGUJuhMOQ_JoKb1jgvziBzv4VE"
        self.chat_id = "6002519484"

        self.last_telegram = 0
        self.telegram_interval = 15

        self.telegram_folder = "telegram_captures"
        os.makedirs(self.telegram_folder, exist_ok=True)

        # ===== INIT =====
        os.makedirs("sounds", exist_ok=True)
        self._init_log()

        pygame.mixer.init()

    def _init_log(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Time", "Object", "Confidence"])

    def set_source(self, source):
        self.stop()
        self.source = source

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()

    def play_alarm(self, label):
        try:
            if not self.alarm_enabled:
                return

            sound_file = self.human_alarm if label == "person" else self.animal_alarm

            if os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
        except Exception as e:
            print("Alarm error:", e)

    def send_telegram_image(self, frame, label, conf):
        try:
            if not self.bot_token or not self.chat_id:
                return

            now = datetime.now()
            date_now = now.strftime("%Y-%m-%d")
            time_now = now.strftime("%H-%M-%S")

            filename = f"{label}_{date_now}_{time_now}.jpg"
            image_path = os.path.join(self.telegram_folder, filename)

            # ✅ compressed image for faster upload
            small_frame = cv2.resize(frame, (640, 480))
            cv2.imwrite(
                image_path,
                small_frame,
                [cv2.IMWRITE_JPEG_QUALITY, 70]
            )

            caption = (
                f"{label}\n detected"f" {date_now}  "
                f" {time_now}"
            )

            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"

            with open(image_path, "rb") as img:
                requests.post(
                    url,
                    data={
                        "chat_id": self.chat_id,
                        "caption": caption
                    },
                    files={"photo": img},
                    timeout=5
                )

        except Exception as e:
            print("Telegram error:", e)

    def get_current_frame(self):
        return self.current_frame

    def get_frames(self):
        self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            print("❌ Camera source not accessible")
            return

        self.running = True
        frame_count = 0

        alert_objects = {"person", "dog", "cat", "bird"}

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            # ✅ smaller size for smooth stream
            frame = cv2.resize(frame, (800, 450))
            self.current_frame = frame.copy()

            frame_count += 1

            # ✅ better FPS optimization
            if frame_count % 3 != 0:
                continue

            results = self.model(frame, conf=self.conf, verbose=False)[0]
            current_time = time.time()
            now = datetime.now()

            for box in results.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = self.model.names[cls]

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"{label} {conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                # ===== LOG EVERY 10 SEC =====
                if current_time - self.last_log >= self.log_interval:
                    with open(self.log_file, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            now.strftime("%Y-%m-%d"),
                            now.strftime("%H:%M:%S"),
                            label,
                            f"{conf:.2f}"
                        ])

                    self.detections.append({
                        "time": now.strftime("%H:%M:%S"),
                        "object": label,
                        "confidence": f"{conf:.2f}"
                    })

                    if len(self.detections) > 100:
                        self.detections.pop(0)

                    self.last_log = current_time

                # ===== ALARM + TELEGRAM =====
                if (
                    self.alarm_enabled
                    and label in alert_objects
                    and current_time - self.last_alarm >= self.alarm_interval
                ):
                    self.play_alarm(label)
                    self.last_alarm = current_time

                    # ✅ NON-BLOCKING TELEGRAM
                    if current_time - self.last_telegram >= self.telegram_interval:
                        frame_copy = frame.copy()

                        threading.Thread(
                            target=self.send_telegram_image,
                            args=(frame_copy, label, conf),
                            daemon=True
                        ).start()

                        self.last_telegram = current_time

            _, buffer = cv2.imencode(".jpg", frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                buffer.tobytes() +
                b"\r\n"
            )

        self.cap.release()