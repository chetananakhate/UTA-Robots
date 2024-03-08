from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from time import time, sleep
from threading import Event
from sqlalchemy.exc import SQLAlchemyError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)
socketio = SocketIO(app)
success_signal_received = False

class User(db.Model):
    username = db.Column(db.String(50), unique=True, nullable=False, primary_key=True)
    password = db.Column(db.String(50), nullable=False)
    devices = db.relationship('Device', backref='user', lazy=True)

class Device(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    os = db.Column(db.String(20), nullable=False)
    socket_id = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)

class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), primary_key=True, nullable=False)
    device_id = db.Column(db.String, db.ForeignKey('device.id'), nullable=False)
    bot_runs = db.relationship('BotRun', backref='bot', lazy=True)

class BotRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    start_time = db.Column(db.String(50), nullable=False)
    end_time = db.Column(db.String(50), nullable=False)
    output_file_path = db.Column(db.String(255))

class AvailableBots(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    dirictory_name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    info_url = db.Column(db.String(255), nullable=False)


# Create the database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return 'Robocorp RPA Bot Manager'

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Check if the username exists
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'Username not found'}), 404

    # Check if the password is correct
    if user.password != password:
        return jsonify({'message': 'Incorrect password'}), 401

    return jsonify({'message': 'Login successful', 'redirect': '/dashboard'})

@app.route('/create_account', methods=['POST'])
def create_account():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Check if the username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'Username already exists'}), 400

    # Create a new user
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Account created successfully', 'redirect': '/login'}), 201

# Endpoint to receive the success signal
@socketio.on("success_signal")
def receive_success_signal():
    global success_signal_received
    success_signal_received = True
    # return jsonify({'message': 'Success signal received'}), 200

@socketio.on("update_session_id")
def update_session_id(data):
    device_id = data.get('device_id')
    print(data)

    device = Device.query.filter_by(id=device_id).first()
    if device:
        device.socket_id = request.sid
        db.session.commit()
        return jsonify({'message': 'Device session_id updated'}), 200
    return jsonify({'message': 'Device not found'}), 404

# @app.route('/register_client_app', methods=['POST'])
@socketio.on("register_client_app")
def register_client_app(data):
    username = data.get('username')
    device_name = data.get('device_name')
    device_id = data.get('device_id')
    os_name = data.get('os')
    print(data)
    print("request.sid: " + request.sid)

    user = Device.query.filter_by(id=device_id).first()
    if user:
        return jsonify({'message': 'Device already present'}), 200

    new_device = Device(id=device_id, name=device_name, os=os_name, user_id=username, socket_id=request.sid)
    db.session.add(new_device)
    print("Trying db.commit")
    try: 
        db.session.commit()
        print("after db.commit")
        return jsonify({'message': 'Client app registered successfully'}), 200
        # socketio.emit('response_from_server', {'message': 'Client app registered successfully'}, room=request.sid)
    except SQLAlchemyError as e:
        db.session.rollback()
        # socketio.emit('response_from_server', {"error": "Commit failed. Error: " + str(e)}, room=request.sid)

    # Emit a response to the client
    # socketio.emit('registration_response', {'status': 'success', 'message': 'Client app registered successfully'})
    # return jsonify({'message': 'Client app registered successfully'}), 200


@app.route('/check_device_registered', methods=['POST'])
def check_device_registered():
    # Get data from the request
    data = request.json
    device_id = data.get('device_id')

    # Check if the user exists
    user = Device.query.filter_by(id=device_id).first()
    if user:
        return jsonify({'message': 'Device already present'}), 200

    return jsonify({'message': 'Device not found'}), 404


@app.route('/get_user_computers/<user_id>', methods=['GET'])
def get_user_computers(user_id):
    print(user_id)
    devices = Device.query.filter_by(user_id=user_id).all()
    computer_data = [{'id': device.id, 'name': device.name.split('.')[0], 'os': device.os} for device in devices]
    return jsonify(computer_data), 200


@app.route('/get_computer_bots/<computer_id>', methods=['GET'])
def get_computer_bots(computer_id):
    print(computer_id)
    bots = Bot.query.filter_by(device_id=computer_id).all()
    bot_data = [{'id': bot.id, 'name': bot.name} for bot in bots]
    return jsonify(bot_data), 200

@app.route('/get_available_bots/<user_id>/<computer_id>', methods=['GET'])
def get_available_bots(user_id, computer_id):
    installed_bots = [bot.name for bot in Bot.query.filter_by(device_id=computer_id).all()]
    available_bots = AvailableBots.query.filter(~AvailableBots.name.in_(installed_bots)).all()
    bot_data = [{'id': bot.id, 'name': bot.name, 'dirictory_name': bot.dirictory_name, 'url': bot.url, 'info_url': bot.info_url} for bot in available_bots]
    return jsonify(bot_data), 200

@app.route('/upload-output', methods=['POST'])
def upload_output():
    bot_run_id = request.form['bot_run_id']
    output_file = request.files['output_file']
    output_file_path = f'path/to/save/{bot_run_id}_output.txt'
    output_file.save(output_file_path)

    bot_run = BotRun.query.filter_by(id=bot_run_id).first()
    if bot_run:
        bot_run.output_file_path = output_file_path
    else:
        new_bot_run = BotRun(id=bot_run_id, output_file_path=output_file_path)
        db.session.add(new_bot_run)
    db.session.commit()

    return 'Output file uploaded successfully', 200


@app.route('/trigger_bot_download/<user_id>/<computer_id>/<bot_id>', methods=['POST'])
def trigger_bot_download(computer_id, bot_id, user_id):
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
    else:
        data = request.json
        computer_id = data.get('computer_id')
        bot_id = data.get('bot_id')
        user_id = data.get('user_id')

        global success_signal_received
        success_signal_received = False

        bot = AvailableBots.query.filter_by(id=bot_id).first()
        if not bot:
            return jsonify({'message': 'Bot not found'}), 404

        # Assuming you have the socket ID stored in your Device table
        device = Device.query.filter_by(id=computer_id).first()
        # get_available_bots = Device.query.filter_by(id=computer_id).first()
        if not device:
            return jsonify({'message': 'Device not found'}), 404
        try:
            socketio.emit('download_robot', {'id': bot.id, 'name': bot.name, 'dirictory_name': bot.dirictory_name, 'url': bot.url}, room=device.socket_id)
            print(f"triggered download success: bot_id({bot.id})")
        except:
            print("triggered download failed")

        print("triggered download")
        
        start_time = time()
        while time() - start_time < 900:
            if success_signal_received:
                print("success_signal_received")
                # new_device = Device(id=device_id, name=device_name, os=os_name, user_id=username, socket_id=request.sid)
                # db.session.add(new_device)
                new_bot = Bot(name=bot.name, device_id=computer_id)
                db.session.add(new_bot)
                db.session.commit()
                return jsonify({'message': 'Download successful'}), 200
            sleep(1)

        return jsonify({'message': 'Download failed (timeout)'}), 408
    
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

    return response

@app.route('/trigger_execute/<user_id>/<computer_id>/<bot_id>', methods=['POST'])
def trigger_bot_execute(computer_id, bot_id, user_id):
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
    else:
        data = request.json
        computer_id = data.get('computer_id')
        bot_id = data.get('bot_id')
        user_id = data.get('user_id')

        global success_signal_received
        success_signal_received = False

        bot = AvailableBots.query.filter_by(id=bot_id).first()
        if not bot:
            return jsonify({'message': 'Bot not found'}), 404

        # Assuming you have the socket ID stored in your Device table
        device = Device.query.filter_by(id=computer_id).first()
        # get_available_bots = Device.query.filter_by(id=computer_id).first()
        if not device:
            return jsonify({'message': 'Device not found'}), 404
        try:
            socketio.emit('execute_robot', {'id': bot.id, 'name': bot.name, 'dirictory_name': bot.dirictory_name, 'url': bot.url}, room=device.socket_id)
            print("triggered execute_robot: {bot.name} success")
        except:
            print(f"triggered execute_robot: {bot.name} failed")
            return jsonify({'message': 'triggered execute_robot: {bot.name} failed'}), 404
            

        start_time = time()
        while time() - start_time < 900:
            if success_signal_received:
                BotRun = BotRun(bot_id=Bot, start_time=' ' , end_time= ' ', output_file_path=' ')
                db.session.add(BotRun)
                return jsonify({'message': 'Robot {bot.name} execute successful'}), 200
            sleep(1)

        return jsonify({'message': 'Robot {bot.name} execute failed (timeout)'}), 408

    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

    return response

@app.route('/trigger_delete', methods=['POST'])
def trigger_bot_delete():
    data = request.json
    user_id = data.get('user_id')
    computer_id = data.get('computer_id')
    robot_id = data.get('robot_id')

    bot = AvailableBots.query.filter_by(id=robot_id).first()
    if not bot:
        return jsonify({'message': 'Bot not found'}), 404

    # Assuming you have the socket ID stored in your WebSocketConnection table
    websocket_connection = Device.query.filter_by(device_id=computer_id).first()
    if not websocket_connection:
        return jsonify({'message': 'WebSocket connection not found'}), 404

    socketio.emit('delete_robot', {'robot_id': robot_id}, room=websocket_connection.socket_id)

    global success_signal_received
    success_signal_received = False
    start_time = time()
    while time() - start_time < 900:
        if success_signal_received:
            return jsonify({'message': 'Bot Delete successful'}), 200
        sleep(1)

    return jsonify({'message': 'Bot Delete failed (timeout)'}), 408



if __name__ == '__main__':
    socketio.run(app, debug=True)
