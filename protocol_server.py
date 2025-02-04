import socket 
import os 
import selectors
from dotenv import load_dotenv
import types

class Server:

    load_dotenv()
    sel = selectors.DefaultSelector()

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print(f"Accepted connection from {addr}")
        # other sockets aren't left waiting when the server isn’t actively working
        conn.setblocking(False)
        # data structure to hold the data that you want included along with the socket
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                print(f"Closing connection to {data.addr}")
                sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print(f"Echoing {data.outb!r} to {data.addr}")
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]

    def handle_client(self): 
        # server-side socket 
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((os.getenv('HOST'), int(os.getenv('PORT'))))
        lsock.listen()
        lsock.setblocking(False)
        # registers the listening socket with the selector 
        self.sel.register(lsock, selectors.EVENT_READ, data=None)
        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    # data keeps track of what has been sent and received on the socket 
                    if key.data is None:
                        # from the listening socket and need to accept the connection 
                        self.accept_wrapper(key.fileobj)
                    else:
                        # from the client socket and need to service the connection 
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            sel.close()
