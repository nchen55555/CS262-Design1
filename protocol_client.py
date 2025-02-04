import socket
import selectors
import types
import threading

sel = selectors.DefaultSelector()

def start_connection(host, port, conn_id):
    """Establish a non-blocking client connection to the server."""
    server_addr = (host, port)
    print(f"Starting client {conn_id} to {server_addr}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(server_addr)  # Non-blocking connect

    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        conn_id=conn_id,
        messages=[b"Hello from client!", b"Another message!"],
        outb=b"",
    )
    sel.register(sock, events, data=data)

def handle_client_io():
    """Handles client socket events for sending and receiving messages."""
    while True:
        events = sel.select(timeout=1)
        for key, mask in events:
            sock = key.fileobj
            data = key.data
            if mask & selectors.EVENT_WRITE and data.messages:
                data.outb = data.messages.pop(0)
                sent = sock.send(data.outb)
                print(f"Client {data.conn_id} sent: {data.outb}")
                data.outb = data.outb[sent:]

            if mask & selectors.EVENT_READ:
                recv_data = sock.recv(1024)
                if recv_data:
                    print(f"Client {data.conn_id} received: {recv_data.decode()}")

def create_clients_dynamically():
    """Allows dynamic creation of new client connections."""
    conn_id = 0
    while True:
        user_input = input("Press Enter to create a new client (or type 'q' to quit): ")
        if user_input.lower() == 'q':
            break
        conn_id += 1
        start_connection("127.0.0.1", 12345, conn_id)

# Start the client event loop in a background thread
threading.Thread(target=handle_client_io, daemon=True).start()

# Accept new clients dynamically
create_clients_dynamically()
