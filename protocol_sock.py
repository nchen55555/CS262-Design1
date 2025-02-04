import socket
import selectors
import types
import threading
from dotenv import load_dotenv
import os
from wire_protocol import packing, unpacking

class ClientSocket(socket): 
    load_dotenv()
    sel = selectors.DefaultSelector()

    def send_message(self, sock, message):
        """Send a custom message to a specific client identified by its socket."""
        # Prepare the message according to wire protocol (if needed)
        data = self.sel.get_key(sock).data  # Access the associated data for the socket
        data.outb = packing(message)
        print(f"Sending message to {sock.getpeername()}: {message}")
        # Modify the socket to handle both reading and writing
        self.sel.modify(sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)
    

    def start_connection(self, host, port, conn_id):
        """Establish a non-blocking client connection to the server."""
        server_addr = (host, port)
        print(f"Starting client {conn_id} to {server_addr}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)  # Non-blocking connect

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(
            conn_id=conn_id,
            # messages=[b"Hello from client!", b"Another message!"],
            outb=b"",
        )
        self.sel.register(sock, events, data=data)

    def handle_client_io(self):
        """Handles client socket events for sending and receiving messages."""
        while True:
            events = self.sel.select(timeout=1)
            for key, mask in events:
                sock = key.fileobj
                data = key.data
                if mask & selectors.EVENT_WRITE and data.outb:
                    # message = data.messages.pop(0)
                    data.outb = # Pack the Message Here According to Wire Protocol 
                    sent = sock.send(data.outb)
                    print(f"Client {data.conn_id} sent: {data.outb}")
                    data.outb = data.outb[sent:]

                if mask & selectors.EVENT_READ:
                    raw_data = sock.recv(1024)
                    if raw_data:
                        version, msg_type, message = unpack_message(raw_data)


    def create_clients_dynamically(self):
        """Allows dynamic creation of new client connections."""
        conn_id = 0
        while True:
            user_input = input("Press Enter to create a new client (or type 'q' to quit): ")
            if user_input.lower() == 'q':
                break
            conn_id += 1
            self.start_connection(os.getenv('HOST'), int(os.getenv('PORT')), conn_id)

    def start(self):
        """Start the client event loop in a background thread."""
        threading.Thread(target=self.handle_client_io, daemon=True).start()

        # Accept new clients dynamically
        self.create_clients_dynamically()

