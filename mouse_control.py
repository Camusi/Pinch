from flask import Flask, request, jsonify
from flask_cors import CORS
import pyautogui

app = Flask(__name__)
CORS(app)

SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

mouse_down = False

print(f"Screen: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
print("Mouse control server running...")
print("Press Ctrl+C to stop.")


@app.route("/gaze", methods=["POST"])
def gaze():

    data = request.json

    if not data:
        return jsonify({"error": "No data"}), 400

    x = float(data.get("x", 0))
    y = float(data.get("y", 0))

    browser_width = float(
        data.get("screenWidth", SCREEN_WIDTH)
    )

    browser_height = float(
        data.get("screenHeight", SCREEN_HEIGHT)
    )

    screen_x = int(
        x * SCREEN_WIDTH / browser_width
    )

    screen_y = int(
        y * SCREEN_HEIGHT / browser_height
    )

    screen_x = max(
        0,
        min(SCREEN_WIDTH - 1, screen_x)
    )

    screen_y = max(
        0,
        min(SCREEN_HEIGHT - 1, screen_y)
    )

    pyautogui.moveTo(
        screen_x,
        screen_y,
        duration=0
    )

    return jsonify({
        "x": screen_x,
        "y": screen_y
    })


@app.route("/mouse-down", methods=["POST"])
def mouse_down_endpoint():

    global mouse_down

    if not mouse_down:

        pyautogui.mouseDown()

        mouse_down = True

        print("MOUSE DOWN")

    return jsonify({
        "success": True
    })


@app.route("/mouse-up", methods=["POST"])
def mouse_up_endpoint():

    global mouse_down

    if mouse_down:

        pyautogui.mouseUp()

        mouse_down = False

        print("MOUSE UP")

    return jsonify({
        "success": True
    })


@app.route("/status")
def status():

    return jsonify({
        "running": True,
        "mouseDown": mouse_down,
        "screenWidth": SCREEN_WIDTH,
        "screenHeight": SCREEN_HEIGHT
    })


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=False
    )