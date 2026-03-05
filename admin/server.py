from flask import Flask, request
import json
import os

app = Flask(__name__)

STATE_FILE = "state.json"

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
    except:
        state = DEFAULT_STATE.copy()

    for key in DEFAULT_STATE:
        if key not in state:
            state[key] = DEFAULT_STATE[key]

    return state


def write_state(data):

    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/")
def home():
    return "LabWall Admin Server Running"


@app.route("/set-mode/<mode>")
def set_mode(mode):

    state = read_state()

    if mode not in ["normal", "lab", "exam"]:
        return {"error": "Invalid mode"}

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

    state = read_state()

    state["clients"][pc_name] = "online"

    write_state(state)

    return {"status": "registered"}


@app.route("/clients")
def clients():

    state = read_state()
    return state["clients"]


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)