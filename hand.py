import cv2
import mediapipe as mp
import math
import threading

from flask import Flask, jsonify
from flask_cors import CORS

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_PATH = "models/hand_landmarker.task"


# ============================================================
# GESTURE SERVER
# ============================================================

app = Flask(__name__)
CORS(app)

gesture = "NONE"


@app.route("/gesture")
def get_gesture():
    return jsonify({
        "gesture": gesture
    })


def start_server():
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )


threading.Thread(
    target=start_server,
    daemon=True
).start()


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

detector = vision.HandLandmarker.create_from_options(options)


# ============================================================
# WEBCAM
# ============================================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

frame_timestamp = 0

print("Pinch detection started.")
print("Gesture server running at:")
print("http://127.0.0.1:5000/gesture")
print("Press Q to quit.")


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read webcam.")
        break

    # Mirror camera
    frame = cv2.flip(frame, 1)

    # Convert BGR -> RGB
    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    frame_timestamp += 1

    result = detector.detect_for_video(
        mp_image,
        frame_timestamp
    )


    # ========================================================
    # DEFAULT GESTURE
    # ========================================================

    gesture = "NONE"


    # ========================================================
    # PROCESS HANDS
    # ========================================================

    if result.hand_landmarks:

        for hand in result.hand_landmarks:

            # Thumb tip = 4
            thumb = hand[4]

            # Index finger tip = 8
            index = hand[8]


            # Convert normalized coordinates to pixels

            thumb_x = int(
                thumb.x * frame.shape[1]
            )

            thumb_y = int(
                thumb.y * frame.shape[0]
            )

            index_x = int(
                index.x * frame.shape[1]
            )

            index_y = int(
                index.y * frame.shape[0]
            )


            # =================================================
            # DISTANCE BETWEEN THUMB + INDEX
            # =================================================

            distance = math.sqrt(
                (thumb_x - index_x) ** 2 +
                (thumb_y - index_y) ** 2
            )


            # =================================================
            # PINCH DETECTION
            # =================================================

            pinch = distance < 40


            if pinch:

                gesture = "PINCH"

                text = "PINCH"

                cv2.putText(
                    frame,
                    text,
                    (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (0, 255, 0),
                    3
                )

            else:

                text = "NO PINCH"

                cv2.putText(
                    frame,
                    text,
                    (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (0, 0, 255),
                    3
                )


            # =================================================
            # DRAW PINCH LINE
            # =================================================

            cv2.line(
                frame,
                (thumb_x, thumb_y),
                (index_x, index_y),
                (255, 0, 0),
                3
            )


            # =================================================
            # DRAW POINTS
            # =================================================

            cv2.circle(
                frame,
                (thumb_x, thumb_y),
                8,
                (255, 0, 0),
                -1
            )

            cv2.circle(
                frame,
                (index_x, index_y),
                8,
                (255, 0, 0),
                -1
            )


            # =================================================
            # ONLY NEED ONE PINCH
            # =================================================

            if pinch:
                break


    # ========================================================
    # DISPLAY CURRENT GESTURE
    # ========================================================

    cv2.putText(
        frame,
        f"Gesture: {gesture}",
        (50, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (255, 255, 255),
        2
    )


    # ========================================================
    # DISPLAY
    # ========================================================

    cv2.imshow(
        "Eye Gesture Control - Pinch Detection",
        frame
    )


    # Q = quit

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ============================================================
# CLEANUP
# ============================================================

camera.release()

cv2.destroyAllWindows()

detector.close()