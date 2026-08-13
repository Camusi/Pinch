// ============================================================
// PINCH / MOUSE CONTROL
// ============================================================

let pinch = false;
let previousPinch = false;

let mouseButtonDown = false;


function processHands(results) {

    pinch = false;


    // --------------------------------------------------------
    // No hand detected
    // --------------------------------------------------------

    if (
        !results ||
        !results.landmarks ||
        results.landmarks.length === 0
    ) {

        // If we were dragging and hand disappears,
        // release the mouse button.

        if (mouseButtonDown) {

            sendMouseAction("up");

            mouseButtonDown = false;
        }

        previousPinch = false;

        return;
    }


    // --------------------------------------------------------
    // Check hands for pinch
    // --------------------------------------------------------

    for (
        const hand of results.landmarks
    ) {

        const thumb =
            hand[4];

        const index =
            hand[8];


        const dx =
            thumb.x -
            index.x;

        const dy =
            thumb.y -
            index.y;

        const dz =
            thumb.z -
            index.z;


        const distance =
            Math.sqrt(
                dx * dx +
                dy * dy +
                dz * dz
            );


        if (
            distance < 0.07
        ) {

            pinch = true;

            break;
        }
    }


    // --------------------------------------------------------
    // Only control mouse in TEST mode
    // --------------------------------------------------------

    if (
        currentMode !== "TEST"
    ) {

        previousPinch = pinch;

        return;
    }


    // --------------------------------------------------------
    // PINCH START
    // --------------------------------------------------------

    if (
        pinch &&
        !previousPinch
    ) {

        console.log(
            "PINCH START"
        );


        sendMouseAction(
            "down"
        );


        mouseButtonDown =
            true;
    }


    // --------------------------------------------------------
    // PINCH RELEASE
    // --------------------------------------------------------

    if (
        !pinch &&
        previousPinch
    ) {

        console.log(
            "PINCH RELEASE"
        );


        sendMouseAction(
            "up"
        );


        mouseButtonDown =
            false;
    }


    previousPinch =
        pinch;


    // --------------------------------------------------------
    // STATUS
    // --------------------------------------------------------

    const info =
        document.getElementById(
            "info"
        );


    if (pinch) {

        info.innerText =
            "PINCH — mouse held";

    }
}


// ============================================================
// SEND MOUSE CLICK / DRAG ACTION
// ============================================================

function sendMouseAction(action) {

    fetch(
        `${MOUSE_SERVER}/click`,
        {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                action: action
            })

        }
    )
    .catch(() => {
        // Ignore occasional connection errors
    });
}