'''Flask Application Business Logic'''
# Import libraries
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random
import time
import logging


# Basic Configurations 
subscriptions = {}      # {symbol: [client_id1, client_id2, ...]}
app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Helper functions for generating random quotes and updating them
def generate_random_quote(symbol):

    # Generate random quote data for simulation (2 DP prices)
    return {
        'symbol': symbol,
        'open': round(random.uniform(100, 200),2),
        'high': round(random.uniform(100, 200),2),
        'low':  round(random.uniform(100, 200),2),
        'bid':  round(random.uniform(100, 200),2),
        'ask':  round(random.uniform(100, 200),2),
    }

def update_quotes():

    # Keep sending quotes to valid symbol and clients while connection is alive for subscribed clients to symbols
    while True:
        for symbol, clients in subscriptions.items():
            quote = generate_random_quote(symbol)
            for client in clients:
                # Send a quote change message to our clients as an acknowledgement
                logger.info(f"Quote emitted for symbol {symbol} to client {client}")
                socketio.emit('quote_change', quote, room=client)
        time.sleep(1)


# Main UI HTML rendering 
@app.route('/')
def index():
    return render_template('client.html')


# Event handler triggered when client subscribe to a new symbol and send data
@socketio.on('subscribe')
def handle_subscribe(data):

    # Based on data received from client, get symbol and client_id
    symbol = data['symbol']
    client_id = request.sid  

    # If symbol is not inside, we add it to our dictionary subscription
    if symbol not in subscriptions:
        subscriptions[symbol] = [client_id]
    # Add client_id inside if symbol exists
    else:
        if client_id not in subscriptions[symbol]:
            subscriptions[symbol].append(client_id)

    # Send a subscription message success to our client as an acknowledgement
    logger.info(f"Client {client_id} subscribed to symbol {symbol}")
    emit('subscription_success', {'symbol': symbol, 'clients': subscriptions[symbol]})
    update_quotes()


# Event handler triggered when client unsubscribe to a new symbol and stop sending data
@socketio.on('unsubscribe')
def handle_unsubscribe(data):

    # Based on data received from client, get symbol and client_id
    symbol = data['symbol']
    client_id = request.sid

    # Remove subscription ONLY IF client has subscribed in the first place
    if symbol in subscriptions and client_id in subscriptions[symbol]:
        subscriptions[symbol].remove(client_id)

    # Send a unsubscription message success to our client as an acknowledgement
    logger.info(f"Client {client_id} unsubscribed from symbol {symbol}")
    emit('unsubscription_success', {'symbol': symbol, 'clients': subscriptions.get(symbol, [])})
    update_quotes()


# Run our Web App
if __name__ == "__main__":
    socketio.run(app, debug=True)
