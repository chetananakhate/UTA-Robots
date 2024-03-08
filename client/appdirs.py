# appdirs.py
import os

def user_config_dir(appname, roaming=False):
    path = os.path.expanduser('~')
    if roaming:
        path = os.path.join(path, 'AppData', 'Roaming')
    else:
        path = os.path.join(path, '.config')
    return os.path.join(path, appname)
