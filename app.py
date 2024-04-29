import os
import uuid
from flask import Flask, render_template, request, send_from_directory, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import random
from string import ascii_uppercase
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
socketio = SocketIO(app)

rooms = {}
user_colors = {}

def generate_unique_code(length):
    while True:
        code = ''.join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            break
    return code

@app.route('/', methods=['POST', 'GET'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        if not name:
            return render_template('home.html', error="Please enter a name", code=code, name=name)
        if join != False and not code:
            return render_template('home.html', error="Please enter a room code", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template('home.html', error="Room does not exist", code=code, name=name)
        
        session['room'] = room
        session['name'] = name
        return redirect(url_for('room'))
    
    return render_template('home.html')

# IMAGE
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return 'No file part'
    file = request.files['image']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = str(uuid.uuid4()) + '.png'
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return 'File uploaded successfully'

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/room')
def room():
    room = session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('home'))
    return render_template('room.html', code=room, messages=rooms[room]["messages"])

# AUDIO
@socketio.on('audio')
def handle_audio(data):
    room = session.get('room')
    name = session.get('name')
    if room not in rooms:
        return
    audio_data = data.get('data')
    if audio_data:
        content = {
            'name': name,
            'audio': audio_data,
            'timestamp': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            'color': user_colors.get(name, 'lightblue')  
        }
        rooms[room]['messages'].append(content)
        emit('audio', content, room=room)

# VIDEO
@socketio.on('video')
def handle_video(data):
    room = session.get('room')
    name = session.get('name')
    if room not in rooms:
        return
    video_data = data.get('data')
    if video_data:
        content = {
            'name': name,
            'video': video_data,
            'timestamp': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            'color': user_colors.get(name, 'lightblue')  
        }
        rooms[room]['messages'].append(content)
        emit('video', content, room=room)

# MESSAGE
@socketio.on('message')
def message(data):
    room = session.get('room')
    if room not in rooms:
        return
    name = session.get('name')
    content = {
        'name': name,
        'message': data['data'],
        'color': user_colors.get(name, 'lightblue')  
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)

# IMAGE
@socketio.on('image')
def handle_image(data):
    room = session.get('room')
    name = session.get('name')
    if room not in rooms:
        return
    image_data = data.get('data')
    if image_data:
        content = {
            'name': name,
            'image': image_data,
            'timestamp': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            'color': user_colors.get(name, 'lightblue')  # Get user's color or default to 'lightblue'
        }
        rooms[room]['messages'].append(content)
        emit('image', content, room=room)

# CONNECT
@socketio.on('connect')
def connect():
    room = session.get('room')
    name = session.get('name')
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    join_room(room)
    send({"name": name, "message": "has joined the room"}, to=room)
    rooms[room]["members"] += 1
    user_colors[name] = generate_random_pastel_color() 
    print(f"{name} joined room {room}")

# DISCONNECT
@socketio.on('disconnect')
def disconnect():
    room = session.get('room')
    name = session.get('name')
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message": "has left the room"}, to=room)
     
    print(f"{name} left room {room}")

import random

def generate_random_pastel_color():
  
    generated_colors = set()

    while True:
        # Create pastel color 
        hue = random.randint(0, 360)
        lightness = random.randint(60, 80)  
        new_color = f"hsl({hue}, 70%, {lightness}%)"
        
        if new_color not in generated_colors:
            generated_colors.add(new_color)
            return new_color


