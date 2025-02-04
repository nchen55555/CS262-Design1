import sys
from protocol_client import Client
from protocol_server import Server

# UI that needs to be implemented (log in, etc)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("please specify running client or server")
    else:
        if sys.argv[1] == "client":
            client = Client()   
            client.start()
        elif sys.argv[1] == "server":
            server = Server()
            server.handle_client()