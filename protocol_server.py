import socket
import os
import selectors
import types
from dotenv import load_dotenv
from wire_protocol import unpacking, packing
from operations import Operations
from user import User
from message import Message
from datetime import datetime
from util import hash_password


class Server:
    load_dotenv()
    sel = selectors.DefaultSelector()
    HEADER = 64
    FORMAT = "utf-8"
    VERSION = "1"

    def __init__(self):
        temp = User("nicole", hash_password("chen"))
        temp_2 = User("michael", hash_password("goat"))
        self.user_login_database = {"nicole": temp, "michael": temp_2}
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
        if sender not in self.user_login_database:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": f"{sender} is not a valid user",
            }
        if receiver not in self.user_login_database:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": f"{receiver} is not a valid user",
            }

        if sender == receiver:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": f"Cannot send a message to yourself",
            }

        if not msg:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": "message is empty",
            }
        message = Message(sender, receiver, msg)
        if receiver not in self.active_users:
            self.user_login_database[receiver].unread_messages.append(message)

        else:
            self.user_login_database[receiver].messages.append(message)

        self.user_login_database[sender].messages.append(message)
        return {
            "version": self.VERSION,
            "type": Operations.SUCCESS.value,
            "info": f"message from {sender} has been sent to {receiver}",
        }

    def read_message(self, username):
        print("Read message", username)
        if username not in self.user_login_database:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": f"{username} is not a valid user",
            }
        try:
            user = self.user_login_database[username]
            if user.unread_messages:
                print("we have unread messages")
                user.messages += user.unread_messages
                user.unread_messages = []

            messages = sorted(user.messages, key=lambda x: x.timestamp)
            messages = [
                f"{msg.sender},{msg.receiver},{msg.timestamp},{msg.message}"
                for msg in messages
            ]
            data = "\n".join([message for message in messages])
            return {
                "version": self.VERSION,
                "type": Operations.SUCCESS.value,
                "info": data,
            }

        except:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": "Read message failed",
            }

    def delete_message(self, sender, receiver, msg, timestamp):
        print("Delete message")
        try:
            if sender in self.user_login_database:
                user = self.user_login_database[sender]
                user.messages = [
                    message
                    for message in user.messages
                    if not (
                        message.receiver == receiver
                        and message.sender == sender
                        and message.message == msg
                        and message.timestamp
                        == datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    )
                ]

            if receiver in self.user_login_database:
                user = self.user_login_database[receiver]
                user.messages = [
                    message
                    for message in user.messages
                    if not (
                        message.receiver == receiver
                        and message.sender == sender
                        and message.message == msg
                        and message.timestamp
                        == datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    )
                ]

                user.unread_messages = [
                    message
                    for message in user.unread_messages
                    if not (
                        message.receiver == receiver
                        and message.sender == sender
                        and message.message == msg
                        and message.timestamp
                        == datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    )
                ]

            return {
                "version": self.VERSION,
                "type": Operations.SUCCESS.value,
                "info": "deleted message successfully",
            }

        except:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": "Delete message failed",
            }

    def delete_account(self, username):
        print("Delete Account", username)
        if username not in self.user_login_database:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": f"{username} is not a valid user",
            }

        try:
            self.user_login_database.pop(username)
            if username in self.active_users:
                self.active_users.pop(username)

            return {
                "version": self.VERSION,
                "type": Operations.SUCCESS.value,
                "info": "Deletion successful",
            }
        except:
            return {
                "version": self.VERSION,
                "type": Operations.FAILURE.value,
                "info": "Deletion of account unsuccessful",
            }

    def service_reads(self, sock, data):
        sock.setblocking(True)
        header_data = sock.recv(self.HEADER).decode(self.FORMAT)
        print("HEADER", header_data)
        if header_data:
            try:
                message_length = int(header_data)
                # recv_data = unpacking(sock.recv(message_length))
                recv_data = b""
                while len(recv_data) < message_length:
                    chunk = sock.recv(message_length - len(recv_data))
                    recv_data += chunk
                recv_data = unpacking(recv_data)
                print("Data received ", recv_data)

                recv_operation = recv_data["type"]
                match recv_operation:
                    case Operations.LOGIN.value:
                        username = recv_data["info"]["username"]
                        password = recv_data["info"]["password"]
                        data.outb = self.login(username, password)
                        result = self.service_writes(sock, data)
                        if result == 0:
                            self.active_users[username] = sock
                            print(f"{username} is now active.")

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

                    case Operations.READ_MESSAGE.value:
                        username = recv_data["info"]
                        data.outb = self.read_message(username)
                        self.service_writes(sock, data)

                    case Operations.DELETE_MESSAGE.value:
                        sender = recv_data["info"]["sender"]
                        receiver = recv_data["info"]["receiver"]
                        msg = recv_data["info"]["msg"]
                        timestamp = recv_data["info"]["timestamp"]
                        data.outb = self.delete_message(
                            sender, receiver, msg, timestamp
                        )
                        self.service_writes(sock, data)

                    case Operations.DELETE_ACCOUNT.value:
                        username = recv_data["info"]
                        data.outb = self.delete_account(username)
                        self.service_writes(sock, data)
            except:
                print("Something failed on the server")

            finally:
                sock.setblocking(False)

        else:
            print(f"Closing connection to {data.addr}")
            self.sel.unregister(sock)
            sock.close()

            for username, user_sock in self.active_users.items():
                if user_sock == sock:
                    del self.active_users[username]
                    print(f"{username} has been removed from active users")
                    break

            sock.setblocking(False)

    def service_writes(self, sock, data):
        try:
            if data.outb:
                serialized_data = packing(data.outb)
                data_length = len(serialized_data)
                header_data = f"{data_length:<{self.HEADER}}".encode(self.FORMAT)
                sock.send(header_data)
                sock.send(serialized_data)
                # Clear the outbound buffer after sending
                data.outb = None
                return 0

            return 1

        except:
            return 1

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
