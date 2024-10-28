from app import socketio
from flask_socketio import emit
from datetime import datetime

@socketio.on('connect')
def handle_connect():
    emit('connection_response', {'data': 'Connected successfully'})

@socketio.on('update_collaboration')
def handle_collaboration_update(data):
    # Broadcast the collaboration update to all connected clients
    emit('collaboration_updated', data, broadcast=True)

@socketio.on('update_opportunity')
def handle_opportunity_update(data):
    # Broadcast the opportunity update to all connected clients
    emit('opportunity_updated', data, broadcast=True)

@socketio.on('new_document')
def handle_new_document(data):
    # Broadcast new document notification to all connected clients
    emit('document_added', data, broadcast=True)
