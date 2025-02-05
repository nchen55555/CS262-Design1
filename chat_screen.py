import sys
from protocol_client import Client
from protocol_server import Server
import selectors
import types
# Global connection ID counter
connection_id = 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please specify running `client` or `server`")
    else:
        if sys.argv[1] == "client":
            sel = selectors.DefaultSelector()
            client = Client(connection_id)
            connection_id += 1
            client.client_socket.connect_ex((client.host, client.port))
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
            sel.register(client.client_socket, events, data=client.data)
        elif sys.argv[1] == "server":
            server = Server()
            server.handle_client()
