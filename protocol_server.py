import socket
import os
import selectors
import types
from dotenv import load_dotenv
from wire_protocol import unpacking, packing
from operations import Operations, Version
from user import User
from message import Message
from datetime import datetime
from util import hash_password
import json
import logging


class Server:
    HEADER = 64
    FORMAT = "utf-8"
    VERSION = "2"
    SEPARATE_CHARACTER = "|"

    def __init__(self):
        load_dotenv()
        temp = User("nicole", hash_password("chen"))
        temp_2 = User("michael", hash_password("goat"))
        # all users and their associated data stored in the User object
        self.user_login_database = {"nicole": temp, "michael": temp_2}

        # all active users and their sockets
        self.active_users = {}  
        self.sel = selectors.DefaultSelector()

    def accept_wrapper(self, sock):
        """
        Accept new clients and register them with the selector.

        socket: the socket object to accept the connection from
        """
        conn, addr = sock.accept()  
        conn.setblocking(False)

        # store connection info
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def check_valid_user(self, username): 
        """
        Checks if the user is in the login database and active users.

        username: the username of the user

        Returns:
            bool: True if the user is in the login database and active users, False otherwise
        """
        # check if the user is in the login database and active users   
        return username in self.user_login_database and username in self.active_users

    def create_data_object(self, version, operation, info):
        """
        Creates a data object with the given version, operation, and info.

        Args:
            version: The version of the data object
            operation: The operation to be performed
            info: information for the data object to pass

        Returns:
            dict: A dictionary representing the data object
        """
        # wraps the json information as a list if it is not already 
        if not isinstance(info, list):
            return {"version": version, "type": operation, "info": [info]}
        else:
            return {"version": version, "type": operation, "info": info}
        
    def unwrap_data_object(self, data): 
        """
        Unwraps the data object if it is a list with only one element. 
        Refuses to unwrap if list has more than one element in the cases 
        of list accounts and read messages.

        data: the data object to be unwrapped

        Returns:
            dict: A dictionary representing the data object
        """
        if len(data["info"]) == 1:
            data["info"] = data["info"][0]
        return data

    def login(self, username, password):
        """
        Logs in the user if the username and password are correct.

        Args:
            username: The username of the user
            password: The password of the user

        Returns:
            dict: A dictionary representing the data object
        """
        # check if the username and password are correct
        if (username in self.user_login_database and self.user_login_database[username].password == password):
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.SUCCESS.value,
                {"message": "Login successful"},
            )
        else:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": "unable to login"},
            )

    def create_account(self, username, password):
        """
        Creates an account if the username and password are not taken.

        Args:
            username: The username of the user
            password: The password of the user

        Returns:
            dict: A dictionary representing the data object
        """
        # check if the username is taken
        if username in self.user_login_database:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": "username is taken"},
            )
        # check if the username and password are not empty
        elif not username or not password:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": "must supply username and password"},
            )
        # create the account
        else:
            self.user_login_database[username] = User(username, password)
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.SUCCESS.value,
                {"message": "Account created"},
            )

    def list_accounts(self, search_string):
        """
        Lists all accounts that start with the search string.

        search_string: The string to search for

        Returns:
            dict: A dictionary representing the data object
        """
        try:
            return self.create_data_object(
                Version.JSON.value,
                Operations.SUCCESS.value,
                [
                    username
                    for username in self.user_login_database.keys()
                    if username.startswith(search_string)
                ]
                ,
            )

        except:
            return self.create_data_object(
                Version.JSON.value,
                Operations.FAILURE.value,
                {"message": "Listing accounts failed"},
            )

    def send_message(self, sender, receiver, msg):  
        """
        Sends a message to the receiver if the sender and receiver are valid users.

        Args:
            sender: The username of the sender
            receiver: The username of the receiver
            msg: The message to send

        Returns:
            dict: A dictionary representing the data object
        """
        # check if the sender is a valid user
        if sender not in self.user_login_database:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": f"{sender} is not a valid user"},
            )   

        # check if the receiver is a valid user
        if receiver not in self.user_login_database:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": f"{receiver} is not a valid user"},
            )

        # check if the sender and receiver are the same
        if sender == receiver:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": "Cannot send a message to yourself"},
            )
        # check if the message is empty
        if not msg: 
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": "message is empty"},
            )

        message = Message(sender, receiver, msg)

        # check if the receiver is active and appends to unread messages if not active and regular messages otherwise
        if receiver not in self.active_users:
            self.user_login_database[receiver].unread_messages.append(message)
        else:
            self.user_login_database[receiver].messages.append(message)

        # append the message to the sender's messages
        self.user_login_database[sender].messages.append(message)

        return self.create_data_object(
            Version.WIRE_PROTOCOL.value,
            Operations.SUCCESS.value,
            {"message": f"message from {sender} has been sent to {receiver}"},
        )

    def read_message(self, username):
        """
        Reads the messages of the user.

        username: The username of the user

        Returns:
            dict: A dictionary representing the data object
        """
        # check if the user is a valid user
        if username not in self.user_login_database:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": f"{username} is not a valid user"},
            )

        try:
            user = self.user_login_database[username]
            # check if the user has unread messages and appends to messages if they do
            if user.unread_messages:
                user.messages += user.unread_messages
                user.unread_messages = []

            # sort the messages by timestamp
            messages = sorted(user.messages, key=lambda x: x.timestamp)
            
            # create the data object as a list of dictionaries that represent the messages
            data = [
                {
                    "sender": msg.sender,
                    "receiver": msg.receiver,
                    "timestamp": str(msg.timestamp),
                    "message": msg.message,
                }
                for msg in messages
            ]
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value, Operations.SUCCESS.value, data
            )

        except:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": "Read message failed"},
            )
        
    def delete_message_from_user(self, user, sender, receiver, msg, timestamp, unread=False):
        """
        Deletes a message from the user's messages and unread messages.

        Args:
            user: The user object
            sender: The username of the sender
            receiver: The username of the receiver
            msg: The message to delete
            timestamp: The timestamp of the message

        Returns:
            list: A list of messages filtered out of the deleted message
        """
        # checks to see if unread messages should also be deleted from the receiver side 
        if unread: 
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

    def delete_message(self, sender, receiver, msg, timestamp):
        """
        Deletes a message from the user's messages and unread messages.

        Args:
            sender: The username of the sender
            receiver: The username of the receiver
            msg: The message to delete
            timestamp: The timestamp of the message

        Returns:
            dict: A dictionary representing the data object
        """
        try:    
            # check if the sender is a valid user
            if sender in self.user_login_database:
                user = self.user_login_database[sender]
                # gets the user and searches for the message to delete
                self.delete_message_from_user(user, sender, receiver, msg, timestamp)
                print("MESSAGES SENDER", user.messages, user.unread_messages)

            # check if the receiver is a valid user and deletes the message from their messages
            if receiver in self.user_login_database:
                user = self.user_login_database[receiver]
                self.delete_message_from_user(user, sender, receiver, msg, timestamp, unread=True)  

            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.SUCCESS.value,
                {"message": "deleted message successfully"},
            )

        except:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": "Delete message failed"},
            )

    def delete_account(self, username):
        """
        Deletes an account from the user login database and active users.

        Args:
            username: The username of the user

        Returns:
            dict: A dictionary representing the data object
        """
        print("DELETING ACCOUNT")
        # check if the user is a valid user
        if username not in self.user_login_database:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": f"{username} is not a valid user"},
            )

        try:
            # deletes the user from the user login database and active users
            print("DELETING ACCOUNT 2")
            self.user_login_database.pop(username)
            if username in self.active_users:
                self.active_users.pop(username)
            print("DELETING ACCOUNT 3")
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.SUCCESS.value,
                {"message": "Deletion successful"},
            )

        except:
            return self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": "Deletion of account unsuccessful"},
            )

    def service_reads(self, sock, data):
        """
        Reads the data from the client and processes the operation, calling service_writes to send the data back to the client.

        sock: The socket object
        data: The data object
        """
        try:
            # receives the header data dictating the length of the incoming data
            header_data = sock.recv(self.HEADER).decode(self.FORMAT)

            if header_data:
                message_length = int(header_data)
                # receives the data from the client and appends it to recv data until the message length is reached
                recv_data = b""
                while len(recv_data) < message_length:
                    chunk = sock.recv(message_length - len(recv_data))
                    recv_data += chunk
                # serializes the data with our wire protocol and unwraps the data object
                recv_data = unpacking(recv_data)
                # unwraps the data object if it is a list with only one element
                recv_data = self.unwrap_data_object(recv_data)
                # gets the operation from the data object
                recv_operation = recv_data["type"]

                match recv_operation:
                    case Operations.LOGIN.value:
                        username = recv_data["info"]["username"]
                        password = recv_data["info"]["password"]
                        data.outb = self.login(username, password)      
                        # checks if the login was successful
                        is_success = data.outb["type"] == Operations.SUCCESS.value
                        # sends the data back to the client
                        print("DATA OUTB: ", data.outb)
                        result = self.service_writes(sock, data)
                        # checks to see if the login was successful with the write to the client 
                        if result == 0 and is_success:
                            # adds the user to the active users
                            self.active_users[username] = sock

                    case Operations.CREATE_ACCOUNT.value:
                        username = recv_data["info"]["username"]
                        password = recv_data["info"]["password"]
                        data.outb = self.create_account(username, password)
                        # sends the data back to the client
                        self.service_writes(sock, data)

                    case Operations.LIST_ACCOUNTS.value:
                        # gets the account search string to find accounts that match the search string
                        search_string = recv_data["info"]["search_string"]
                        data.outb = self.list_accounts(search_string)
                        # sends the data back to the client
                        self.service_writes(sock, data)

                    case Operations.SEND_MESSAGE.value: 
                        sender = recv_data["info"]["sender"]
                        receiver = recv_data["info"]["receiver"]
                        msg = recv_data["info"]["message"]
                        data.outb = self.send_message(sender, receiver, msg)
                        # checks to see if the receiver is active and sends the message with the receiver socket 
                        # for instantaneous messaging 
                        if receiver in self.active_users:
                            receiver_conn = self.active_users[receiver]
                            # creates the data object to deliver instantaneous messages 
                            msg_data_receiver = self.create_data_object(
                                Version.WIRE_PROTOCOL.value,
                                Operations.DELIVER_MESSAGE_NOW.value,
                                {"message": f"From {sender}: {msg}"},
                            )

                            # serializes the data object and sends it to the receiver
                            serialized_data = packing(msg_data_receiver)
                            data_length = len(serialized_data)
                            header_data = f"{data_length:<{self.HEADER}}".encode(
                                self.FORMAT
                            )
                            receiver_conn.send(header_data)
                            receiver_conn.send(serialized_data)
                        # sends the data back to the client   
                        self.service_writes(sock, data)

                    case Operations.READ_MESSAGE.value:
                        username = recv_data["info"]["username"]
                        data.outb = self.read_message(username)
                        # sends the data back to the client
                        self.service_writes(sock, data)

                    case Operations.DELETE_MESSAGE.value:
                        sender = recv_data["info"]["sender"]
                        receiver = recv_data["info"]["receiver"]
                        msg = recv_data["info"]["message"]
                        timestamp = recv_data["info"]["timestamp"]
                        data.outb = self.delete_message(
                            sender, receiver, msg, timestamp
                        )
                        # sends the data back to the client
                        self.service_writes(sock, data)

                    case Operations.DELETE_ACCOUNT.value:
                        username = recv_data["info"]["username"]
                        if not self.check_valid_user(username):
                            # checks to see if the user initiating the action is valid in the edge case 
                            # where the user is not in the user login database
                            logging.info(f"Closing connection to {data.addr}")
                            self.sel.unregister(sock)
                            sock.close()
                        data.outb = self.delete_account(username)
                        # sends the data back to the client
                        self.service_writes(sock, data)

            else:
                logging.error(f"Closing connection to {data.addr}")
                # closes the sockets and unregisters the socket from the selector
                self.sel.unregister(sock)
                sock.close()
                # deletes the user from the active users
                for username, user_sock in self.active_users.items():
                    if user_sock == sock:
                        del self.active_users[username]
                        logging.info(f"{username} has been removed from active users")
                        break

        except Exception as e:
            data.outb = self.create_data_object(
                Version.WIRE_PROTOCOL.value,
                Operations.FAILURE.value,
                {"message": f"Exception in service_reads {e}"},
            )
            self.service_writes(sock, data)

    def service_writes(self, sock, data):
        """
        Writes the data to the client.

        sock: The socket object
        data: The data object

        Returns: 0 upon success 1 if there is an error
        """
        try:
            if data.outb:
                # checks to see the versioning of the data object and serializes it accordingly
                if data.outb["version"] == Version.WIRE_PROTOCOL.value:
                    serialized_data = packing(data.outb)
                else:
                    json_data = json.dumps(data.outb).encode(self.FORMAT)
                    serialized_data = (
                        data.outb["version"].encode(self.FORMAT) + json_data
                    )
                data_length = len(serialized_data)
                header_data = f"{data_length:<{self.HEADER}}".encode(self.FORMAT)
                sock.send(header_data)
                sock.send(serialized_data)
                # Clear the outbound buffer after sending
                data.outb = None
                return 0
            return 0  

        except Exception as e:  
            print(f"Error in service_writes: {e}")
            data.outb = None  
            return 1

    def service_connection(self, key, mask):
        """
        Handles reading and writing for a connected client.

        key: The key object
        mask: The mask object
        """
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            self.service_reads(sock, data)
        if mask & selectors.EVENT_WRITE:
            self.service_writes(sock, data)

    def handle_client(self):
        """
        Starts the server and handles client connections.
        """
        # instantiates the listening socket 
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((os.getenv("HOST"), int(os.getenv("PORT"))))
        lsock.listen()
        lsock.setblocking(False)
        self.sel.register(lsock, selectors.EVENT_READ, data=None)

        try:
            while True:     
                # selects the events from the selector
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    # listening socket commands to create a new client connection 
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    # client socket commands to handle the client connection
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            logging.error("Caught keyboard interrupt, exiting")
        finally:
            self.sel.close()
