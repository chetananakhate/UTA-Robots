import os
import platform
import socket
import subprocess
import sys
import appdirs
import requests
from tkinter import *
import tkinter as tk
from tkinter import Tk
from tkinter import messagebox
import yaml
import pystray
from pystray import MenuItem as item
from PIL import Image
from flask import Flask, render_template
from flask_socketio import SocketIO
from zipfile import ZipFile
import shutil
import hashlib
import logging
from engineio.async_drivers import threading
import socketio
import sqlite3
import time 
from apscheduler.schedulers.background import BackgroundScheduler

"""def create_db():
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  bot_id TEXT,
                  name TEXT,
                  directory_name TEXT,
                  url TEXT,
                  interval INTEGER)''')
    conn.commit()
    conn.close()

create_db()"""


# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

ROBOTS_DIRECTORY = os.environ.get('APPDATA') or (os.path.expanduser('~/Library/Preferences/robot-data/robots') if os.name == 'posix' else os.path.expanduser('~/.local/share/robot-data/robots'))
FLASK_URL = "http://127.0.0.1:5000"

app = Flask(__name__)
# socketio = SocketIO(app, async_mode="threading")
# Create a SocketIO client
sio = socketio.Client()

# Connect to the Flask-SocketIO server
# sio.connect(FLASK_URL)
    

@sio.on("download_robot")
def handle_download_robot(data):
    print("Download bot request received")
    robot_id = data["id"]
    name = data["name"]
    dirictory_name = data["dirictory_name"]
    url = data["url"]
    
    download_rcc_bot(robot_id, name, dirictory_name, url)

@sio.on("delete_robot")
def handle_delete_robot(data):
    print("Delete bot request received")
    robot_id = data["id"]
    name = data["name"]
    dirictory_name = data["dirictory_name"]
    url = data["url"]

    delete_rcc_bot(robot_id, name, dirictory_name, url)

@sio.on("execute_robot")
def handle_execute_robot(data):
    print("Execute bot request received")
    robot_id = data["id"]
    name = data["name"]
    dirictory_name = data["dirictory_name"]
    url = data["url"]
    
    
    execute_rcc_bot(robot_id, name, dirictory_name, url)

def download_rcc_bot(bot_id, name, dirictory_name, url):
    folder_path = os.path.join(str(ROBOTS_DIRECTORY), str(bot_id))
    file_path = os.path.join(folder_path, str(dirictory_name))
    print(f"file_path: {file_path}")

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    response = requests.get(url, stream=True)

    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=128):
            file.write(chunk)

    unzip_robot(file_path, folder_path)

    logging.info(f"Robot {name} downloaded and unzipped successfully")
    print(f"Robot {name} downloaded and unzipped successfully")
    sio.emit("success_signal")
    return {"status": "success", "message": "Robot downloaded and unzipped successfully"}


def execute_rcc_bot(bot_id, name, dirictory_name, url):
    folder_path = os.path.join(str(ROBOTS_DIRECTORY), str(bot_id))
    dirictory_name = "".join(dirictory_name.split())
    file_path = os.path.join(folder_path, str(dirictory_name))
    print(f"file_path: {file_path}")

    # Run the rcc command based on the platform
    if sys.platform == 'win32':
        command = f"cd /d {file_path} && rcc run"
    else:
        command = f"cd {file_path} && rcc run"

    # Run the command
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print("rcc run completed successfully")
        print(result.stdout)
    else:
        print("Error running rcc run:")
        print(result.stderr)
    
    print("Execution Success")
    sio.emit("success_signal")
    return {"status": "success", "message": "Robot Executed successfully"}


"""
    # Upload output file to backend
    output_file_path = os.path.join(folder_path, "output.txt")
    with open(output_file_path, "rb") as file:
        files = {"file": file}
        response = requests.post(FLASK_URL+'/upload-output', files=files)

        if response.status_code == 200:
            logging.info("Output file uploaded successfully")
        else:
            logging.error("Failed to upload output file")

    return {"status": "success", "message": "Tasks executed and output file uploaded successfully"}

"""

def delete_rcc_bot(robot_id):
    folder_path = os.path.join(ROBOTS_DIRECTORY, robot_id)
    shutil.rmtree(folder_path, ignore_errors=True)

    logging.info(f"Robot {robot_id} deleted successfully")
    
    return {"status": "success", "message": "Robot deleted successfully"}


def unzip_robot(zip_file_path, extract_to):
    with ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

def install_rcc():
    system = platform.system()
    if system == 'Windows':
        # Download RCC
        os.system('curl -o rcc.exe https://downloads.robocorp.com/rcc/releases/latest/windows64/rcc.exe')
        # Add RCC to system path (assumes user has permission)
        os.system('setx PATH "%PATH%;%cd%"')
    elif system == 'Darwin':  # macOS
        # Update brew
        os.system('brew update')
        # Install RCC
        os.system('brew install robocorp/tools/rcc')
    elif system == 'Linux':
        # Download RCC
        os.system('curl -o rcc https://downloads.robocorp.com/rcc/releases/latest/linux64/rcc')
        # Make the downloaded file executable
        os.system('chmod a+x rcc')
        # Add RCC to path (requires sudo)
        os.system('sudo mv rcc /usr/local/bin/')
    else:
        logging.error(f"Unsupported operating system: {system}")
        sys.exit(1)

    # Test RCC installation
    result = subprocess.run(['rcc', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        logging.info(f"RCC installed successfully. Version: {result.stdout.strip()}")
    else:
        logging.error("Failed to install RCC.")
        sys.exit(1)

def show_register_window():
    global root, username_entry, password_entry

    root = tk.Tk()
    root.title("Login")
    root.geometry("300x150")

    tk.Label(root, text="Username:").pack()
    username_entry = tk.Entry(root)
    username_entry.pack()

    tk.Label(root, text="Password:").pack()
    password_entry = tk.Entry(root, show="*")
    password_entry.pack()

    tk.Button(root, text="Login", command=login).pack()
    
    mainloop()
    # root.iconify()

# Function to handle login
def login():
    username = username_entry.get()
    password = password_entry.get()

    response = requests.post(FLASK_URL+'/login', json={'username': username, 'password': password})
    data = response.json()

    if response.status_code == 200:
        messagebox.showinfo("Login", data['message'])

        # Register the client app after successful login
        register_client_app(username, password)
        # if is_logged_in():
        root.withdraw()
        start_app()
    else:
        messagebox.showerror("Login Failed", data['message'])

def register_client_app(username, password):
    print("calling register_client_app")
    os_name = os.uname().sysname if os.name == 'posix' else os.name
    if sys.platform == 'win32':
        device_name = os.getenv('COMPUTERNAME')
        serial = os.getenv('COMPUTERNAME') + os.getenv('PROCESSOR_IDENTIFIER') + os.getenv('USERDOMAIN')
        device_id = hashlib.md5(serial.encode()).hexdigest()
    
    elif sys.platform == 'darwin':
        device_name = socket.gethostname()
        serial = subprocess.check_output("ioreg -l | grep IOPlatformSerialNumber", shell=True).decode("utf-8")
        device_id = hashlib.md5(serial.encode()).hexdigest()
    
    elif sys.platform.startswith('linux'):
        device_name = socket.gethostname()
        serial = subprocess.check_output("dmidecode -s system-uuid", shell=True).decode("utf-8")
        device_id = hashlib.md5(serial.encode()).hexdigest()

    # sio.connect(FLASK_URL)
    print("before emit")

    # try:
    sio.emit('register_client_app',data = {
        'device_id': device_id,
        'os': os_name,
        'device_name': device_name,
        'username': username
    })
    #     messagebox.showinfo("Client App Registration Success")
    # except:
    #     messagebox.showerror("Client App Registration Failed")

    # sio.wait()
    

# Register event handlers for other SocketIO events if needed
# For example, handling the response from the backend after registration
@sio.on('registration_response')
def on_registration_response(data=None):
    print(data)
    if data and isinstance(data, dict) and data.get('message'):
        if data.get('status') == 'success':
            messagebox.showinfo("Client App Registered", data['message'])
        else:
            messagebox.showerror("Client App Registration Failed", data['message'])
    else:
        messagebox.showerror("Client App Registration Failed", "Unknown error occurred.")

"""
def schedule_jobs():
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute('SELECT * FROM jobs')
    jobs = c.fetchall()
    conn.close()

    scheduler = BackgroundScheduler()
    for job in jobs:
        bot_id, name, directory_name, url, interval = job
        scheduler.add_job(execute_rcc_bot, 'interval', minutes=interval, args=(bot_id, name, directory_name, url))
    scheduler.start()

@sio.on('add_job_to_db')
def add_job_to_db(bot_id, name, directory_name, url, interval):
    conn = sqlite3.connect('scheduler.db')
    c = conn.cursor()
    c.execute('INSERT INTO jobs (bot_id, name, directory_name, url, interval) VALUES (?, ?, ?, ?, ?)',
              (bot_id, name, directory_name, url, interval))
    conn.commit()
    conn.close()
"""


# Function to start the app
def start_app():
    print(f"ROBOTS_DIRECTORY: {ROBOTS_DIRECTORY}")
    global tray_icon
    print("app started")
    image = Image.open("./UTA_logo.png")
    menu = (item('Exit', lambda: exit()),)
    tray_icon = pystray.Icon("UTA Robots App", image, "", menu)
    # schedule_jobs()
    tray_icon.run()
    root.mainloop()
    


def exit():
    os._exit(0)

def is_logged_in():

    if sys.platform == 'win32':
        serial = os.getenv('COMPUTERNAME') + os.getenv('PROCESSOR_IDENTIFIER') + os.getenv('USERDOMAIN')
        device_id = hashlib.md5(serial.encode()).hexdigest()
    
    elif sys.platform == 'darwin':
        serial = subprocess.check_output("ioreg -l | grep IOPlatformSerialNumber", shell=True).decode("utf-8")
        device_id = hashlib.md5(serial.encode()).hexdigest()
    
    elif sys.platform.startswith('linux'):
        serial = subprocess.check_output("dmidecode -s system-uuid", shell=True).decode("utf-8")
        device_id = hashlib.md5(serial.encode()).hexdigest()

    # Check if the login status is stored
    response = requests.post(FLASK_URL+'/check_device_registered', json={'device_id': device_id})
    
    if response.status_code == 200:
        sio.emit('update_session_id',data = {
        'device_id': device_id
        })
        print("update_session_id")
        return True
    else:
        return False

def main():
    # sio.run(app, debug=False, port=5001)
    sio.connect(FLASK_URL)
    if is_logged_in():
        start_app()
    else:
        install_rcc()
        show_register_window()

    # Register the app to start on login
    if sys.platform == 'win32':
        import winreg

        app_name = "UTA Robots App"
        app_path = sys.executable
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
            winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, app_path)

    elif sys.platform == 'darwin':
        import plistlib

        app_name = "UTA Robots App"
        app_path = sys.executable
        plist_path = os.path.expanduser(f'~/Library/LaunchAgents/{app_name}.plist')
        plist_content = {
            'Label': app_name,
            'ProgramArguments': [app_path],
            'RunAtLoad': True
        }
        with open(plist_path, 'wb') as plist_file:
            plistlib.dump(plist_content, plist_file)

    elif sys.platform.startswith('linux'):
        import subprocess

        app_name = "UTA Robots App"
        app_path = sys.executable
        autostart_dir = appdirs.user_config_dir("autostart", roaming=True)
        autostart_path = os.path.join(autostart_dir, f"{app_name}.desktop")
        autostart_content = f"""[Desktop Entry]
        Type=Application
        Exec={app_path}
        Hidden=false
        X-GNOME-Autostart-enabled=true
        Name[en_US]={app_name}
        Name={app_name}
        Comment[en_US]=Start {app_name} at login
        Comment=Start {app_name} at login"""
        with open(autostart_path, 'w') as autostart_file:
            autostart_file.write(autostart_content)
            autostart_file.flush()
            os.fsync(autostart_file.fileno())

if __name__ == '__main__':
    main()


# pyinstaller --onefile --add-data "appdirs.py:." --name uta_robots main.py
# ./dist/uta_robots