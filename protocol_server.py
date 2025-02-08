import socket
import os
import selectors
import types
from dotenv import load_dotenv
from wire_protocol import unpacking, packing
from operations import Operations
from user import User
from message import Message


class Server:
    load_dotenv()
    sel = selectors.DefaultSelector()
    HEADER = 64
    FORMAT = "utf-8"
    VERSION = "1"

    def __init__(self):
        temp = User("nicole", "chen")
        self.user_login_database = {"nicole": temp}
        self.active_users = {}  # username mapped to the socket connection

    def accept_wrapper(self, sock):
        """Accept new clients and register them with the selector."""
        conn, addr = sock.accept()  # Should be ready to read
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)

        # Store connection info
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def login(self, username, password):
        print("login", username, password)
        if (
            username in self.user_login_database
            and self.user_login_database[username].password == password
        ):
            return {
                "version": self.VERSION,
                "type": Operations.SUCCESS.value,
                "info": "",
            }
        else:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": "unable to login",
            }

    def create_account(self, username, password):
        print("create account", username, password)
        if username in self.user_login_database:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": "Username is taken",
            }
        elif not username or not password:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": "Must supply username and password",
            }
        else:
            self.user_login_database[username] = User(username, password)
            return {
                "version": self.VERSION,
                "type": Operations.SUCCESS.value,
                "info": "Account created",
            }

    def list_accounts(self, search_string):
        print("Search accounts", search_string)
        try:
            return {
                "version": self.VERSION,
                "type": Operations.SUCCESS.value,
                "info": ", ".join(
                    [
                        username
                        for username in self.user_login_database.keys()
                        if username.startswith(search_string)
                    ]
                ),
            }

        except:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": "Listing accounts failed",
            }

    def send_message(self, sender, receiver, msg):
        print("sending message")
        if receiver not in self.user_login_database:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": f"{receiver} is not a valid user",
            }

        elif not msg:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": "message is empty",
            }

        if receiver not in self.active_users:
            self.user_login_database[receiver].unread_messages.append(
                f"From {sender}: {msg}"
            )

        return {
            "version": self.VERSION,
            "type": Operations.SUCCESS.value,
            "info": f"message from {sender} has been sent to {receiver}",
        }

    def service_reads(self, sock, data):
        header_data = sock.recv(self.HEADER).decode(self.FORMAT)
        print("HEADER", header_data)
        if header_data:
            message_length = int(header_data)
            recv_data = unpacking(sock.recv(message_length))  # Read incoming data

            recv_operation = recv_data["type"]
            match recv_operation:
                case Operations.LOGIN.value:
                    print("HERE", recv_data)
                    username = recv_data["info"]["username"]
                    password = recv_data["info"]["password"]
                    data.outb = self.login(username, password)
                    self.service_writes(sock, data)

                case Operations.CREATE_ACCOUNT.value:
                    username = recv_data["info"]["username"]
                    password = recv_data["info"]["password"]
                    data.outb = self.create_account(username, password)
                    self.service_writes(sock, data)

                case Operations.LIST_ACCOUNTS.value:
                    search_string = recv_data["info"]
                    data.outb = self.list_accounts(search_string)
                    self.service_writes(sock, data)

                case Operations.SEND_MESSAGE.value:
                    sender = recv_data["info"]["sender"]
                    receiver = recv_data["info"]["receiver"]
                    msg = recv_data["info"]["msg"]
                    data.outb = self.send_message(sender, receiver, msg)
                    if receiver in self.active_users:
                        receiver_conn = self.active_users[receiver]
                        msg_data = {
                            "version": self.VERSION,
                            "type": Operations.SUCCESS.value,
                            "info": f"From {sender}: {msg}",
                        }
                        serialized_data = packing(msg_data)
                        data_length = len(serialized_data)
                        header_data = f"{data_length:<{self.HEADER}}".encode(
                            self.FORMAT
                        )
                        receiver_conn.send(header_data)
                        receiver_conn.send(serialized_data)

                    self.service_writes(sock, data)

        else:
            print(f"Closing connection to {data.addr}")
            self.sel.unregister(sock)
            sock.close()

    def service_writes(self, sock, data):
        if data.outb:
            serialized_data = packing(data.outb)
            data_length = len(serialized_data)
            header_data = f"{data_length:<{self.HEADER}}".encode(self.FORMAT)
            sock.send(header_data)
            sock.send(serialized_data)
            # Clear the outbound buffer after sending
            data.outb = None

    # TODO: #2 create server functions to handle all of these operations
    def service_connection(self, key, mask):
        """Handles reading and writing for a connected client."""
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            # unpack here
            self.service_reads(sock, data)
        if mask & selectors.EVENT_WRITE:
            self.service_writes(sock, data)

    def handle_client(self):
        """Starts the server and handles client connections."""
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((os.getenv("HOST"), int(os.getenv("PORT"))))
        lsock.listen()
        lsock.setblocking(False)
        self.sel.register(lsock, selectors.EVENT_READ, data=None)

        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    # listening socket
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    # client socket
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self.sel.close()
