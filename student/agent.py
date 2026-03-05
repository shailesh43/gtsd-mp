import requests
import time
import socket
import subprocess
import psutil

from config import ADMIN_SERVER, CHECK_INTERVAL

pc_name = socket.gethostname()

last_mode = None
site_opened = False


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


def heartbeat():

    try:
        requests.post(
            f"{ADMIN_SERVER}/heartbeat",
            json={"pc_name": pc_name},
            timeout=3
        )
    except:
        pass


def fetch_rules():

    try:
        r = requests.get(f"{ADMIN_SERVER}/rules", timeout=3)
        return r.json()

    except:
        return None


SAFE_PROCESSES = [
    "system","idle","explorer.exe","winlogon.exe","csrss.exe",
    "services.exe","lsass.exe","svchost.exe","dwm.exe",
    "python.exe","cmd.exe","bash.exe","powershell.exe",
    "conhost.exe",
    "runtimebroker.exe",
    "searchhost.exe",
    "startmenuexperiencehost.exe",
    "shellexperiencehost.exe",
    "textinputhost.exe"
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
                print(f"Killing unauthorized process: {name}")
                proc.kill()

        except:
            pass


def kill_chrome():

    for proc in psutil.process_iter(["name"]):

        try:
            if proc.info["name"] and proc.info["name"].lower() == "chrome.exe":
                proc.kill()
        except:
            pass


def open_sites(sites):

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    subprocess.Popen([chrome_path] + sites)


def normal_mode():

    print("Normal mode active")


def lab_mode(rules):

    global site_opened

    allowed_apps = rules["lab_allowed_apps"] + ["chrome.exe", "explorer.exe"]

    kill_unallowed(allowed_apps)

    sites = rules["lab_allowed_websites"]

    if sites and not site_opened:

        print("Opening allowed lab websites")

        kill_chrome()

        open_sites(sites)

        site_opened = True


def exam_mode(rules):

    global site_opened

    allowed_apps = ["chrome.exe", "explorer.exe"]

    kill_unallowed(allowed_apps)

    sites = rules["exam_allowed_websites"]

    if sites and not site_opened:

        print("Opening exam website")

        kill_chrome()

        open_sites(sites)

        site_opened = True


def main():

    global last_mode
    global site_opened

    register()

    while True:

        heartbeat()

        rules = fetch_rules()

        if not rules:
            time.sleep(CHECK_INTERVAL)
            continue

        mode = rules["mode"]

        if mode != last_mode:
            print(f"\nMode changed → {mode}")
            site_opened = False
            last_mode = mode

        if mode == "normal":
            normal_mode()

        elif mode == "lab":
            lab_mode(rules)

        elif mode == "exam":
            exam_mode(rules)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()