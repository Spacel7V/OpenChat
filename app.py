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

# Mot de passe VIP haché (hashed 'wang140815&')
VIP_PASSWORD_HASH = hashlib.sha256(b'wang140815&').hexdigest()

# Modèle de base de données pour les messages
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Crée la base de données et les tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', messages=messages)

# Gestion des messages
@socketio.on('message')
def handleMessage(data):
    username = data['username']
    message = data['message']
    timestamp = data['timestamp']

    # Vérification si l'utilisateur est VIP (serveur seulement)

    # Sauvegarde le message dans la base de données
    new_message = Message(username=username, message=message)
    db.session.add(new_message)
    db.session.commit()

    # Envoie le message à tous les utilisateurs
    send({'username': username, 'message': message, 'timestamp': timestamp}, broadcast=True)

@socketio.on('check password')
def check_password(password_attempt):
    hashed_attempt = hashlib.sha256(password_attempt.encode()).hexdigest()
    if hashed_attempt == VIP_PASSWORD_HASH:
        emit('password valid', broadcast=False)
    else:
        emit('password invalid', broadcast=False)


# Gestion de l'effacement des messages (VIP uniquement)
@socketio.on('clear messages')
def clearMessages():
    # Si l'utilisateur est VIP, effacer les messages
    emit('messages cleared', broadcast=True)
    db.session.query(Message).delete()  # Supprimer tous les messages de la base de données
    db.session.commit()


# Comptage des utilisateurs en ligne
connected_users = 0

@socketio.on('connect')
def handle_connect():
    global connected_users
    connected_users += 1
    
    # Récupérer les anciens messages de la base de données
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    message_list = [{'username': msg.username, 'message': msg.message, 'timestamp': msg.timestamp.strftime('%H:%M:%S'), 'vip': '[VIP]' in msg.username} for msg in messages]
    
    # Envoyer les anciens messages à l'utilisateur connecté
    emit('load previous messages', message_list)

    # Diffuser le nombre d'utilisateurs connectés
    emit('update user count', connected_users, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global connected_users
    connected_users -= 1
    emit('update user count', connected_users, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)
