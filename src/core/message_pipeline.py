from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
import logging
from typing import Dict, Any

class HTTPMessagePipeline:
    """
    Simple HTTP-based message pipeline.
    """

    def __init__(self, host='localhost', port=8000, logger=None):
         self.host = host
         self.port = port
         self.server = None
         self.running = False
         if logger:
            self.logger = logger
         else:
            self.logger = logging.getLogger("http_message_pipeline")
            self.logger.setLevel(logging.DEBUG) # Default log level can be changed as needed
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
         self.message_handlers = {} # store handlers for messages
         self.server_thread = None # store the server thread

    def start(self):
        """
        Start the http server
        """
        if self.running:
            self.logger.warning("Server already running, ignoring command")
            return
        self.server = HTTPServer((self.host, self.port), _HTTPRequestHandler)
        self.server.message_pipeline = self
        self.running = True
        self.logger.info(f"Message Pipeline listening on http://{self.host}:{self.port}")
        # Start the server in a new thread to not block the main program
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True # So that the thread closes when the main program closes
        self.server_thread.start()

    def stop(self):
        """
        Stop the http server
        """
        if not self.running:
             self.logger.warning("Server not running, ignoring command")
             return

        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join() # Wait for the server to close fully
        self.running = False
        self.logger.info("Message Pipeline stopped.")

    def subscribe(self, message_type: str, handler):
        """
        Subscribe to a certain type of message
        """
        if message_type in self.message_handlers:
             self.message_handlers[message_type].append(handler)
        else:
             self.message_handlers[message_type] = [handler]
        self.logger.info(f"Subscribed to message type: {message_type}")


    def unsubscribe(self, message_type: str, handler):
        """
        Unsubscribe from message type
        """
        if message_type in self.message_handlers and handler in self.message_handlers[message_type]:
            self.message_handlers[message_type].remove(handler)
            self.logger.info(f"Unsubscribed from message type: {message_type}")
        else:
            self.logger.warning(f"No handler '{handler}' subscribed to message type: {message_type}")

    def publish(self, message_type: str, message_data: Dict[str, Any]):
        """
        Publish a message to subscribers.
        """
        if message_type in self.message_handlers:
            for handler in self.message_handlers[message_type]:
                handler(message_data)
            self.logger.debug(f"Published message of type '{message_type}': {message_data}")
        else:
            self.logger.debug(f"No subscribers for message type: {message_type}, message not sent.")
        
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self):
        self.stop()

class _HTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Handler for incoming HTTP requests.
    """
    def do_POST(self):
        """
        Handle incoming POST requests.
        """
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            message = json.loads(post_data.decode('utf-8'))
            if 'type' not in message or 'data' not in message:
                 self.send_response(400)
                 self.send_header("Content-Type", "application/json")
                 self.end_headers()
                 response_message = {'error': 'Request missing "type" or "data" property'}
                 self.wfile.write(json.dumps(response_message).encode('utf-8'))
                 return
            
            message_type = message['type']
            message_data = message['data']
            
            self.server.message_pipeline.publish(message_type, message_data) # Send the message to any subscribers
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response_message = {'message': 'Successfully sent message to subscribers'}
            self.wfile.write(json.dumps(response_message).encode('utf-8'))
        except Exception as e:
             self.send_response(500)
             self.send_header("Content-Type", "application/json")
             self.end_headers()
             response_message = {'error': f'Error receiving message: {e}'}
             self.wfile.write(json.dumps(response_message).encode('utf-8'))

    def log_message(self, format, *args):
        """Override default log_message to send output to our logger"""
        self.server.message_pipeline.logger.info(f'{self.address_string()} - {format%args}')