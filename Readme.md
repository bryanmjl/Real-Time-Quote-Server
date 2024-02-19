## Real Time Quote Server

### A. About
This project is about designing a real time quote server which aims to replicate providing simulated stock prices to clients. Some of the design features implemented are:
1. Clients should be able to subscribe ticker from some time and then any change
in quotation (open, high, low, bid , ask ) for that symbol should be provided to the
subscriber
2. Data transfer should be real-time, and application should support multiple
ticket subscriptions from single or multiple clients
3. Client can interact via a server interface and receive stock quotes


### B. Tech stacks and Workflow
We use the following tech stacks:
1. ```Flask``` and ```Python```: Backend Flask Web Application
2. ```Flask_socketio```: Birectional Websocket TCP communication for Flask Applications between Client and Server
3. ```HTML``` and ```JavaScript```: Flask Client UI webpage rendering and JS functions (Client -> Server)

Overview of event workflow for real time quote server:
1. App deployment
    - The Flask application ```app.py``` is deployed, and the Socket.IO server is initiated.
    - The server starts listening for incoming connections.
2. Client clicks on subscribe button in HTML page
    - The user enters a symbol in the "Subscribe to Symbol" input field and clicks the "Subscribe" button
    - The ```subscribe()``` JavaScript function is triggered
    - The ```socket.emit('subscribe', { symbol: symbol })``` line sends a 'subscribe' event to the server`
    - On the server side, the ```@socketio.on('subscribe')``` event handler is triggered
    - The server updates the ```subscriptions``` dictionary, emits a 'subscription_success' event to the client, and logs the subscription
    - The client receives the ```'subscription_success'``` event and then logs a message indicating a successful subscription
3. Once subscribed, quotes comes in continuosly to simulate real time pricing data
    - On the server side, the ```update_quotes``` function periodically generates random quotes for subscribed symbols and emits ```'quote_change'``` events to the respective clients
    - Clients that are subscribed to symbols receive the ```'quote_change'``` event
    - The ```displayQuote``` JavaScript function is called, updating the client's UI with the new quote
    - When a client receives a ```'quote_change'``` event, the ```displayQuote``` function is called to update the UI with the new quote
4. If client clicks on unsubscribe:
    - Similar to subscribe workflow BUT IF the client has previously subscribed to a symbol, now they will stop receiving quotes

### c. Technical Implementation
1. Server side implementation ```app.py```
    - Import the following libraries for our app:
        - ```
          from flask import Flask, render_template, request
          from flask_socketio import SocketIO, emit
          import random
          import time
          import logging
          ```
    - Initialise our Web app and web sockets. Create loggers for tracking purposes
        - ```
          subscriptions = {}      # {symbol: [client_id1, client_id2, ...]}
          app = Flask(__name__)
          socketio = SocketIO(app, async_mode="threading")
          logging.basicConfig(level=logging.INFO)
          logger = logging.getLogger(__name__)
          ```
    - Define a flask route to render main HTML webpage per ```Templates/client.html```
        - ```
          @app.route('/')
          def index():
              return render_template('client.html')
          ```
    - Create helper functions ```generate_random_quote``` and ```update_quotes```. These helper functions are used in our main event handlers later
        - ```
            def generate_random_quote(symbol):

                # Generate random quote data for demonstration
                return {
                    'symbol': symbol,
                    'open': round(random.uniform(100, 200),2),
                    'high': round(random.uniform(100, 200),2),
                    'low':  round(random.uniform(100, 200),2),
                    'bid':  round(random.uniform(100, 200),2),
                    'ask':  round(random.uniform(100, 200),2),
                }

            def update_quotes():

                # Keep sending quotes to valid symbol and clients while connection is alive
                while True:
                    for symbol, clients in subscriptions.items():
                        quote = generate_random_quote(symbol)
                        for client in clients:
                            # Send a quote change message to our clients as an acknowledgement
                            socketio.emit('quote_change', quote, room=client)
                            logger.info(f"Quote emitted for symbol {symbol} to client {client}")
                    time.sleep(1)
          ```

    - Create our event handlers ```subscribe``` and ```unsubscribe``` to listen for events sent from client to server side. See step on client side implementation for actual code blocks. Our event handlers are denoted by decorators ```@socketio.on('subscribe')``` and ```@socketio.on('unsubscribe')```
        
2. Client Side implementation ```client.py```
    - Create header, Subscribe/Unsubscribe to symbol text, as well as our main title on ```Templates/client.html```

    - Create websocket connection between client and server side and URL for users to load
        - ```
          var socket = io.connect('http://' + document.domain + ':' + location.port);
          ```
    - Create a JS function ```subscribe()``` which gets called when the subscribe button is clicked on client webpage. If symbol is not empty, it emits a "subscribe" event to the backend server function
        - ```
            # Front end JS function
            function subscribe() {
                        var symbol = document.getElementById('subscribe-symbol').value;
                        if (symbol.trim() !== '') {
                            socket.emit('subscribe', { symbol: symbol });
                        }
                    }

            # Backend Flask function
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
                emit('subscription_success', {'symbol': symbol, 'clients': subscriptions[symbol]})
                logger.info(f"Client {client_id} subscribed to symbol {symbol}")
                update_quotes()
            ```
    - Create a JS function ``` unsubscribe``` which gets called when the unsubscribe button is clicked on webpage. This sents a "unsubscribe" event to the backend server function
        - ```
            # Front end JS function
            function unsubscribe() {
                        var symbol = document.getElementById('unsubscribe-symbol').value;
                        if (symbol.trim() !== '') {
                            socket.emit('unsubscribe', { symbol: symbol });
                        }
                    }

            # Backend Flask function
            @socketio.on('unsubscribe')
            def handle_unsubscribe(data):

                # Based on data received from client, get symbol and client_id
                symbol = data['symbol']
                client_id = request.sid

                # Remove subscription ONLY IF client has subscribed in the first place
                if symbol in subscriptions and client_id in subscriptions[symbol]:
                    subscriptions[symbol].remove(client_id)

                # Send a unsubscription message success to our client as an acknowledgement
                emit('unsubscription_success', {'symbol': symbol, 'clients': subscriptions.get(symbol, [])})
                logger.info(f"Client {client_id} unsubscribed from symbol {symbol}")
                update_quotes()
            ```
    - Create an event listener for ```quote_change``` which will then actually display prices on the UI for clients to see
        - ```
            socket.on('quote_change', function (quote) {
                displayQuote(quote);
            });
          ```
    - Create other event listeners for ```subscription_success``` and ```unsubscription_success``` which logs a message to console depending on type of event
        - ```
            socket.on('subscription_success', function (data) {
                console.log('Subscribed to symbol:', data.symbol, 'Current clients:', data.clients);
            });

            socket.on('unsubscription_success', function (data) {
                console.log('Unsubscribed from symbol:', data.symbol, 'Current clients:', data.clients);
            });

          ```