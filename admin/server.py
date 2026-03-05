from flask import Flask, request
import json
import time

app = Flask(__name__)

STATE_FILE = "state.json"

# A client is considered offline if no heartbeat received within this many seconds.
# Should be a multiple of CHECK_INTERVAL on the agent side (which is 5s).
OFFLINE_THRESHOLD = 15

DEFAULT_STATE = {
    "mode": "normal",
    "clients": {},

    "lab_allowed_apps": [],
    "lab_allowed_websites": [],

    "exam_allowed_apps": ["chrome.exe"],
    "exam_allowed_websites": []
}


def read_state():
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except Exception:
        state = DEFAULT_STATE.copy()

    for key in DEFAULT_STATE:
        if key not in state:
            state[key] = DEFAULT_STATE[key]

    return state


def write_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_client_statuses(clients):
    """
    Returns a dict: { pc_name: "online" | "offline" }
    A client is online if its last heartbeat timestamp is within OFFLINE_THRESHOLD seconds.
    Clients that registered but never sent a heartbeat (value == "online" string) are shown as online
    briefly, then will go offline once the threshold passes without a numeric timestamp.
    """
    now = time.time()
    statuses = {}
    for name, last_seen in clients.items():
        if isinstance(last_seen, (int, float)):
            statuses[name] = "online" if (now - last_seen) <= OFFLINE_THRESHOLD else "offline"
        else:
            # Legacy string value from initial registration — treat as recently online
            statuses[name] = "online"
    return statuses


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return "LabWall Admin Server Running"


@app.route("/set-mode/<mode>")
def set_mode(mode):
    state = read_state()
    if mode not in ["normal", "lab", "exam"]:
        return {"error": "Invalid mode"}, 400
    state["mode"] = mode
    write_state(state)
    return {"status": "success", "mode": mode}


@app.route("/get-mode")
def get_mode():
    state = read_state()
    return {"mode": state["mode"]}


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    pc_name = data.get("pc_name")
    if not pc_name:
        return {"error": "pc_name required"}, 400

    state = read_state()
    # Store timestamp immediately so the threshold logic applies from the start
    state["clients"][pc_name] = time.time()
    write_state(state)

    return {"status": "registered"}


@app.route("/clients")
def clients():
    """
    Returns each client with a clear online/offline status and last-seen time.
    """
    state = read_state()
    statuses = get_client_statuses(state["clients"])
    now = time.time()

    result = {}
    for name, last_seen in state["clients"].items():
        if isinstance(last_seen, (int, float)):
            seconds_ago = int(now - last_seen)
            result[name] = {
                "status": statuses[name],
                "last_seen_seconds_ago": seconds_ago
            }
        else:
            result[name] = {
                "status": "online",
                "last_seen_seconds_ago": None
            }

    return result


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json
    pc_name = data.get("pc_name")
    if not pc_name:
        return {"error": "pc_name required"}, 400

    state = read_state()
    state["clients"][pc_name] = time.time()
    write_state(state)

    return {"status": "alive"}


@app.route("/rules")
def rules():
    state = read_state()
    return {
        "mode": state["mode"],
        "lab_allowed_apps": state["lab_allowed_apps"],
        "lab_allowed_websites": state["lab_allowed_websites"],
        "exam_allowed_apps": state["exam_allowed_apps"],
        "exam_allowed_websites": state["exam_allowed_websites"]
    }


@app.route("/set-rules", methods=["POST"])
def set_rules():
    """
    Update allowed apps/websites for a given mode without changing the mode itself.
    Expects JSON body with any subset of:
      lab_allowed_apps, lab_allowed_websites, exam_allowed_apps, exam_allowed_websites
    """
    data = request.json
    state = read_state()

    updatable = ["lab_allowed_apps", "lab_allowed_websites", "exam_allowed_apps", "exam_allowed_websites"]
    for key in updatable:
        if key in data:
            state[key] = data[key]

    write_state(state)
    return {"status": "rules updated"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)