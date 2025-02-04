import socket
import selectors
import types
import threading
from dotenv import load_dotenv
import os

class Client:
    def __init__(self, conn_id):
        self.host = os.getenv('HOST')
        self.port = int(os.getenv('PORT'))
        self.conn_id = conn_id
        self.sel = selectors.DefaultSelector()
        self.sock = None

    def start_connection(self):
        """Connect to the server and start communication."""
        server_addr = (self.host, self.port)
        print(f"Client {self.conn_id}: Connecting to {server_addr}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)  # Non-blocking connect
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(conn_id=self.conn_id, outb=b"")
        self.sel.register(sock, events, data=data)

        return sock, data

    # TODO: #1 create client functions send message, login, delete account, etc. - follows format here 
    def send_message(self, message):
        """Send a custom message to the server."""
        data = self.sel.get_key(self.sock).data
        data.outb = message.encode()
        self.sel.modify(self.sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)

    def handle_client_io(self):
        """Handle sending and receiving messages for this client."""
        while True:
            events = self.sel.select(timeout=1)  # Wait for events
            for key, mask in events:
                sock = key.fileobj
                data = key.data
                if mask & selectors.EVENT_WRITE and data.outb:
                    sent = sock.send(data.outb)  # Send data
                    print(f"Client {data.conn_id}: Sent message: {data.outb.decode()}")
                    data.outb = data.outb[sent:]  # Clear the sent data

                if mask & selectors.EVENT_READ:
                    recv_data = sock.recv(1024)  # Read response from server
                    if recv_data:
                        print(f"Client {data.conn_id}: Received: {recv_data.decode()}")
                    else:
                        # Connection closed by the server
                        print(f"Client {data.conn_id}: Connection closed by server")
                        self.sel.unregister(sock)
                        sock.close()

    def start(self):
        """Initialize client and run the event loop."""
        sock, data = self.start_connection()
        self.sock = sock
