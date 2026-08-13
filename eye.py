import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_PATH = "models/face_landmarker.task"


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1,
    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

detector = vision.FaceLandmarker.create_from_options(options)


# ============================================================
# IRIS LANDMARKS
# ============================================================

LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]


# ============================================================
# EYE GAZE CALCULATION
# ============================================================

def calculate_eye_gaze(
        face,
        iris_indices,
        eye_corners,
        upper_lid,
        lower_lid
):

    # -----------------------------------------
    # Eye corners
    # -----------------------------------------

    corner1 = face[eye_corners[0]]
    corner2 = face[eye_corners[1]]

    corner1_x = corner1.x
    corner2_x = corner2.x

    # -----------------------------------------
    # Iris center
    # -----------------------------------------

    iris_x = sum(
        face[i].x for i in iris_indices
    ) / len(iris_indices)

    iris_y = sum(
        face[i].y for i in iris_indices
    ) / len(iris_indices)

    # -----------------------------------------
    # Eye horizontal position
    # -----------------------------------------

    left_x = min(
        corner1_x,
        corner2_x
    )

    right_x = max(
        corner1_x,
        corner2_x
    )

    eye_width = right_x - left_x

    # -----------------------------------------
    # Eyelid positions
    # -----------------------------------------

    upper_y = sum(
        face[i].y for i in upper_lid
    ) / len(upper_lid)

    lower_y = sum(
        face[i].y for i in lower_lid
    ) / len(lower_lid)

    top_y = min(
        upper_y,
        lower_y
    )

    bottom_y = max(
        upper_y,
        lower_y
    )

    eye_height = bottom_y - top_y

    # -----------------------------------------
    # Safety check
    # -----------------------------------------

    if eye_width < 0.001 or eye_height < 0.001:

        return 0.5, 0.5, iris_x, iris_y

    # -----------------------------------------
    # Normalize
    # -----------------------------------------

    horizontal = (
        iris_x - left_x
    ) / eye_width

    vertical = (
        iris_y - top_y
    ) / eye_height

    # Keep values between 0 and 1
    horizontal = max(
        0.0,
        min(1.0, horizontal)
    )

    vertical = max(
        0.0,
        min(1.0, vertical)
    )

    return (
        horizontal,
        vertical,
        iris_x,
        iris_y
    )


# ============================================================
# CAMERA
# ============================================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():

    print("ERROR: Could not open webcam.")

    detector.close()

    exit()


timestamp = 0

print("Gaze tracking started.")
print("Look around with your eyes.")
print("Press Q to quit.")


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    success, frame = camera.read()

    if not success:

        print("ERROR: Could not read webcam.")

        break

    # Mirror webcam
    frame = cv2.flip(
        frame,
        1
    )

    height, width = frame.shape[:2]

    # BGR → RGB
    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    timestamp += 1

    result = detector.detect_for_video(
        mp_image,
        timestamp
    )


    # ========================================================
    # FACE DETECTED
    # ========================================================

    if result.face_landmarks:

        face = result.face_landmarks[0]


        # ----------------------------------------------------
        # LEFT EYE
        # ----------------------------------------------------

        left_x, left_y, left_iris_x, left_iris_y = calculate_eye_gaze(

            face,

            LEFT_IRIS,

            [263, 362],

            [386, 387, 388],

            [374, 380, 381]
        )


        # ----------------------------------------------------
        # RIGHT EYE
        # ----------------------------------------------------

        right_x, right_y, right_iris_x, right_iris_y = calculate_eye_gaze(

            face,

            RIGHT_IRIS,

            [33, 133],

            [159, 160, 161],

            [145, 153, 154]
        )


        # ----------------------------------------------------
        # AVERAGE BOTH EYES
        # ----------------------------------------------------

        gaze_x = (
            left_x +
            right_x
        ) / 2

        gaze_y = (
            left_y +
            right_y
        ) / 2


        # ----------------------------------------------------
        # DETERMINE DIRECTION
        # ----------------------------------------------------

        if gaze_x < 0.35:

            horizontal = "LEFT"

        elif gaze_x > 0.65:

            horizontal = "RIGHT"

        else:

            horizontal = "CENTER"


        if gaze_y < 0.35:

            vertical = "UP"

        elif gaze_y > 0.65:

            vertical = "DOWN"

        else:

            vertical = "CENTER"


        # ====================================================
        # DISPLAY NUMBERS
        # ====================================================

        cv2.putText(
            frame,
            f"X: {gaze_x:.3f}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Y: {gaze_y:.3f}",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            f"{horizontal}",
            (30, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"{vertical}",
            (30, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )


        # ====================================================
        # DRAW IRIS
        # ====================================================

        cv2.circle(
            frame,
            (
                int(left_iris_x * width),
                int(left_iris_y * height)
            ),
            6,
            (0, 0, 255),
            -1
        )

        cv2.circle(
            frame,
            (
                int(right_iris_x * width),
                int(right_iris_y * height)
            ),
            6,
            (0, 0, 255),
            -1
        )


    # ========================================================
    # SHOW
    # ========================================================

    cv2.imshow(
        "Eye Gesture Control - Gaze Test",
        frame
    )


    # Q quits
    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

camera.release()

cv2.destroyAllWindows()

detector.close()