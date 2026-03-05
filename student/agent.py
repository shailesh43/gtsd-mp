import requests
import time
import socket
import subprocess
import psutil

from config import ADMIN_SERVER, CHECK_INTERVAL

pc_name = socket.gethostname()


def register():

    try:
        requests.post(
            f"{ADMIN_SERVER}/register",
            json={"pc_name": pc_name},
            timeout=3
        )
        print("Registered with admin")

    except:
        print("Server not reachable")


def fetch_rules():

    try:
        r = requests.get(f"{ADMIN_SERVER}/rules", timeout=3)
        return r.json()

    except:
        return None


SAFE_PROCESSES = [
    "system",
    "idle",
    "explorer.exe",
    "winlogon.exe",
    "csrss.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "dwm.exe",
    "python.exe",
    "cmd.exe",
    "bash.exe",
    "powershell.exe",
    "conhost.exe",
    
    # VS code insiders
    "code - insiders.exe",
    "node.exe",
    "pylance"
]

def kill_unallowed(allowed):

    allowed = [a.lower() for a in allowed]

    for proc in psutil.process_iter(["pid", "name"]):

        try:
            name = proc.info["name"]

            if not name:
                continue

            name = name.lower()

            if name in SAFE_PROCESSES:
                continue

            if name not in allowed:
                proc.kill()

        except:
            pass

def ensure_chrome():

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    running = False

    for proc in psutil.process_iter(["name"]):

        if proc.info["name"] and proc.info["name"].lower() == "chrome.exe":
            running = True

    if not running:
        subprocess.Popen(chrome_path)


def normal_mode():

    print("Normal mode active")


def lab_mode(rules):

    allowed_apps = rules["lab_allowed_apps"]

    print("Lab mode active")

    kill_unallowed(allowed_apps)


def exam_mode():

    allowed_apps = ["chrome.exe", "explorer.exe"]

    print("Exam mode active")

    kill_unallowed(allowed_apps)

    ensure_chrome()


def main():

    register()

    while True:

        rules = fetch_rules()

        if not rules:
            time.sleep(CHECK_INTERVAL)
            continue

        mode = rules["mode"]

        if mode == "normal":
            normal_mode()

        elif mode == "lab":
            lab_mode(rules)

        elif mode == "exam":
            exam_mode()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()