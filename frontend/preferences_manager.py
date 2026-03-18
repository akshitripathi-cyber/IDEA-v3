import json
import os

def get_preferences_path():
    home = os.path.expanduser("~")
    pref_dir = os.path.join(home, "IDEA")

    os.makedirs(pref_dir, exist_ok=True)

    return os.path.join(pref_dir, "preferences.json")


def save_preferences(name, data):
    path = get_preferences_path()

    prefs = {}

    if os.path.exists(path):
        with open(path, "r") as f:
            prefs = json.load(f)

    prefs[name] = data

    with open(path, "w") as f:
        json.dump(prefs, f, indent=4)


def load_preferences():
    path = get_preferences_path()

    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


def delete_preference(name):
    path = get_preferences_path()

    if not os.path.exists(path):
        return

    with open(path, "r") as f:
        prefs = json.load(f)

    if name in prefs:
        del prefs[name]

    with open(path, "w") as f:
        json.dump(prefs, f, indent=4)