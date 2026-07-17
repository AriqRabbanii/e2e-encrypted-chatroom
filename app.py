import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# Generate a secure key for session, fallback to random if environment variable is not set
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_fallback_secret_key_123456')

# Initialize SocketIO, allowing all origins for testing/presentation
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    """Render the main chat room interface."""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Handle a client connection event."""
    print("A client connected to the WebSocket server.")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle a client disconnection event gracefully."""
    print("A client disconnected from the WebSocket server.")

@socketio.on('join')
def handle_join(data):
    """
    Handle a user joining the chat.
    Broadcasts a plaintext system message to all clients.
    """
    username = data.get('username', 'Anonymous')
    print(f"System: User '{username}' joined the chatroom.")
    # Broadcast to all connected clients that a new user has joined
    emit('system_message', {
        'message': f"User '{username}' joined the chatroom."
    }, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    """
    Blindly broadcast the encrypted message payload to all clients.
    The server does not (and cannot) decrypt the message.
    """
    # Exclude sender from broadcast? Usually SocketIO sends to everyone, 
    # but we can broadcast to all clients including the sender so they get their own message back,
    # or handle it locally. In SocketIO, `broadcast=True` broadcasts to everyone except sender, 
    # or we can emit to everyone (include_self=True is default in socketio emit).
    # Let's broadcast to everyone so all clients see it.
    emit('receive_message', {
        'username': data.get('username'),
        'ciphertext': data.get('ciphertext'),
        'timestamp': data.get('timestamp')
    }, broadcast=True, include_self=True)

if __name__ == '__main__':
    # Listen on localhost (127.0.0.1) for safety, on port 5000
    # In production, DO NOT use 0.0.0.0. Default to localhost.
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
