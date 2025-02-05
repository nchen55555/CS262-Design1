import socket
import selectors
import types
import threading
from dotenv import load_dotenv
import os


class Client:
    def __init__(self, conn_id):
        self.host = os.getenv("HOST")
        self.port = int(os.getenv("PORT"))
        self.conn_id = conn_id
        self.sel = selectors.DefaultSelector()
        self.sock = None

    def start_connection(self):
        """Connect to the server and wait until ready."""
        server_addr = (self.host, self.port)
        print(f"Client {self.conn_id}: Connecting to {server_addr}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)

        # attempt non-blocking connection
        result = sock.connect_ex(server_addr)
        if result not in (0, socket.errno.EINPROGRESS):
            print(f"Client {self.conn_id}: Connection failed, error {result}")
            sock.close()
            return None, None

        # wait for the socket to be connected
        sel = selectors.DefaultSelector()
        sel.register(sock, selectors.EVENT_WRITE)
        ready = sel.select(timeout=5)

        if not ready:
            print(f"Client {self.conn_id}: Connection timeout")
            sock.close()
            return None, None

        sel.unregister(sock)

        # register socket for reading/writing
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(conn_id=self.conn_id, outb=b"")
        self.sel.register(sock, events, data=data)

        return sock, data

    # TODO: #1 create client functions send message, login, delete account, etc. - follows format here
    def send_message(self, message):
        """Send a custom message to the server."""
        data = self.sel.get_key(self.sock).data
        data.outb = message.encode()
        self.sel.modify(
            self.sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data
        )

    def handle_client_io(self):
        """Handle sending and receiving messages for this client."""
        while self.sock:
            # ait for activity
            events = self.sel.select(timeout=1)
            if not events:
                continue

            for key, mask in events:
                sock = key.fileobj
                data = key.data

                if mask & selectors.EVENT_WRITE and data.outb:
                    try:
                        sent = sock.send(data.outb)
                        print(
                            f"Client {data.conn_id}: Sent message: {data.outb.decode()}"
                        )
                        data.outb = data.outb[sent:]
                    except BrokenPipeError:
                        print(f"Client {data.conn_id}: Server closed connection")
                        self.cleanup(sock)
                        return

                if mask & selectors.EVENT_READ:
                    try:
                        recv_data = sock.recv(1024)
                        if recv_data:
                            print(
                                f"Client {data.conn_id}: Received: {recv_data.decode()}"
                            )
                        else:
                            print(f"Client {data.conn_id}: Server closed connection")
                            self.cleanup(sock)
                            return
                    except ConnectionResetError:
                        print(f"Client {data.conn_id}: Connection reset by server")
                        self.cleanup(sock)
                        return

    def cleanup(self, sock):
        """Unregister and close the socket."""
        try:
            self.sel.unregister(sock)
        except Exception:
            pass
        sock.close()
        self.sock = None

    def start(self):
        """Initialize client and run the event loop."""
        sock, data = self.start_connection()
        if sock is None:
            print(f"Client {self.conn_id}: Could not connect to server.")
            return

        self.sock = sock

        # start the IO handler in a separate thread
        io_thread = threading.Thread(target=self.handle_client_io, daemon=True)
        io_thread.start()

        # keep main thread alive
        while self.sock:
            try:
                message = input(f"Client {self.conn_id} > ")
                if message.lower() == "exit":
                    print(f"Client {self.conn_id}: Exiting.")
                    self.cleanup(self.sock)
                    break
                self.send_message(message)
            except KeyboardInterrupt:
                print(f"\nClient {self.conn_id}: Interrupted. Exiting.")
                self.cleanup(self.sock)
                break
