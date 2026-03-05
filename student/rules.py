import requests
from config import ADMIN_SERVER


def fetch_rules():

    try:
        r = requests.get(f"{ADMIN_SERVER}/rules", timeout=3)
        return r.json()

    except:
        return None