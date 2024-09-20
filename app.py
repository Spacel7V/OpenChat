import hashlib
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, send, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Hash SHA-256 du mot de passe VIP ("wang140815&")
VIP_PASSWORD_HASH = hashlib.sha256(b"wang140815&").hexdigest()

# Modèle de base de données pour les messages
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Crée la base de données et les tables
with app.app_context():
    db.create_all()

# Gestion des messages
@socketio.on('message')
def handleMessage(data):
    username = data['username']
    message = data['message']
    timestamp = data['timestamp']
    vip_status = data['vip']

    # Sauvegarde le message dans la base de données
    new_message = Message(username=username, message=message)
    db.session.add(new_message)
    db.session.commit()

    # Envoie le message à tous les utilisateurs
    send({'username': username, 'message': message, 'timestamp': timestamp, 'vip': vip_status}, broadcast=True)

# Gestion de l'effacement des messages (VIP uniquement)
@socketio.on('clear messages')
def clearMessages():
    # Supprime tous les messages dans la base de données
    db.session.query(Message).delete()
    db.session.commit()
    emit('messages cleared', broadcast=True)

# Gestion du mot de passe VIP haché
@socketio.on('check password')
def check_password(data):
    password = data['password']
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    if hashed_password == VIP_PASSWORD_HASH:
        emit('password correct', {'vip': True})
    else:
        emit('password incorrect', {'vip': False})

# Compteur d'utilisateurs connectés hehe
connected_users = 0

@socketio.on('connect')
def on_connect():
    global connected_users
    connected_users += 1
    emit('user count', {'count': connected_users}, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    global connected_users
    connected_users -= 1
    emit('user count', {'count': connected_users}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
