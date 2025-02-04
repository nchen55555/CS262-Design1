import socket
import os
import selectors
import types
from dotenv import load_dotenv

class Server:
    load_dotenv()
    sel = selectors.DefaultSelector()

    def accept_wrapper(self, sock):
        """Accept new clients and register them with the selector."""
        conn, addr = sock.accept()  # Should be ready to read
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)

        # Store connection info
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def service_connection(self, key, mask):
        """Handles reading and writing for a connected client."""
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Read incoming data
            if recv_data:
                data.outb += recv_data  # Echo the data
            else:
                print(f"Closing connection to {data.addr}")
                self.sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                sent = sock.send(data.outb)
                print(f"Echoing {data.outb!r} to {data.addr}")
                data.outb = data.outb[sent:]

    def handle_client(self):
        """Starts the server and handles client connections."""
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((os.getenv('HOST'), int(os.getenv('PORT'))))
        lsock.listen()
        lsock.setblocking(False)
        self.sel.register(lsock, selectors.EVENT_READ, data=None)

        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self.sel.close()


if __name__ == "__main__":
    server = Server()
    server.handle_client()
