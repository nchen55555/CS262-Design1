import socket
import os
from protos import app_pb2
from wire_protocol import packing, unpacking
from operations import Operations, OperationNames, Version
from util import hash_password
import threading
import logging
import json
from dotenv import load_dotenv


class Client:
    # global variables consistent across all instances of the Client class
    FORMAT = "utf-8"
    HEADER = 64

    # polling thread to handle incoming messages from the server
    CLIENT_LOCK = threading.Lock()

    def __init__(self, stub):
        load_dotenv()
        self.host = os.getenv("HOST")
        self.port = int(os.getenv("PORT"))
        self.stub = stub

        # username of the current client
        self.username = ""

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
        return {"version": version, "type": operation, "info": [info]}

    def unwrap_data_object(self, data):
        """
        Unwraps the data object to return the info field if it is a single element list.
        Specific to the case where the operation is not reading messages or listing accounts.

        Args:
            data: The data object to unwrap

        Returns:
            dict: The info field from the data object
        """
        if data and len(data["info"]) == 1:
            data["info"] = data["info"][0]
        return data

    def login(self, username, password):
        """
        Handles the login process for the client application.
        Prompts the user for their username and password, hashes the password,
        and sends the login request to the server.

        Args:
            username: The username of the client
            password: The password of the client
        Returns:
            bool: True if login is successful, False otherwise
        """
        # hash password
        password = hash_password(password)
        print("HELLO", password)
        res = self.stub.RPCLogin(app_pb2.Response(info=[username, password]))
        status = res.operation

        if status == app_pb2.SUCCESS:
            self.username = username
            unread_messages = int(res.info)
            return True, int(unread_messages)

        return False, 0

    def create_account(self, username, password):
        """
        Handles the account creation process for the client application.
        Prompts the user for a unique username and password, hashes the password,
        and sends the account creation request to the server.

        Args:
            username: The username of the client
            password: The password of the client

        Returns:
            bool: True if account creation is successful, False otherwise
        """
        password = hash_password(password)

        # create the data object to send to the server, specifying the version number, operation type, and info
        data = self.create_data_object(
            self.protocol_version,
            Operations.CREATE_ACCOUNT.value,
            {"username": username, "password": password},
        )

        data_received = self.client_send(data)
        data_received = self.unwrap_data_object(data_received)

        if data_received and data_received["type"] == Operations.SUCCESS.value:
            self.username = username
            return True

        # if the data received for account creation is not successful, print the error message
        elif data_received and data_received["type"] == Operations.FAILURE.value:
            logging.error(f"Cannot create account: {data_received['info']}")
        else:
            logging.error("Account Creation Failed. Try again.")

        return False

    def list_accounts(self, search_string):
        """
        Handles the account listing process for the client application.
        Prompts the user for a search string and sends the account listing request to the server.

        Args:
            search_string: The search string to search for in the accounts

        Returns:
            list: The list of accounts that match the search string
        """
        data = self.create_data_object(
            self.protocol_version,
            Operations.LIST_ACCOUNTS.value,
            {"search_string": search_string},
        )

        data_received = self.client_send(data)

        if data_received and data_received["type"] == Operations.SUCCESS.value:
            accounts = data_received["info"]
            return [] if accounts == [""] else accounts

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            logging.error(f"Cannot List Accounts: {data_received['info']}")
        else:
            logging.error("Listing accounts failed. Try again.")

        return

    def send_message(self, receiver, msg):
        """
        Handles the message sending process for the client application.
        Prompts the user for the receiver's username and the message content,
        and sends the message request to the server.

        Args:
            receiver: The receiver of the message
            msg: The message content

        Returns:
            bool: True if message sending is successful, False otherwise
        """
        data = self.create_data_object(
            self.protocol_version,
            Operations.SEND_MESSAGE.value,
            {"sender": self.username, "receiver": receiver, "message": msg},
        )
        # sends the data object to the server and receives the response in data_received
        data_received = self.client_send(data)
        # unwraps the data object to return the info field
        data_received = self.unwrap_data_object(data_received)

        if data_received and data_received["type"] == Operations.SUCCESS.value:
            return True

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            logging.error(f"Message sending failure: {data_received['info']}")
        else:
            logging.error("Sending message failed. Try again.")

        return False

    def read_message(self):
        """s
        Handles the message reading process for the client application.
        Sends a request to the server to read all messages for the current user.

        Returns:
            list: The list of messages for the current user
        """
        try:
            data = self.create_data_object(
                self.protocol_version,
                Operations.READ_MESSAGE.value,
                {"username": self.username},
            )

            try:
                data_received = self.client_send(data)
            except ConnectionError as e:
                logging.error(f"Connection error while reading messages: {e}")
                return
            except socket.timeout as e:
                logging.error(f"Socket timeout while reading messages: {e}")
                return

            if data_received and data_received["type"] == Operations.SUCCESS.value:
                messages = data_received["info"] if data_received["info"] else []
                return messages

            elif data_received and data_received["type"] == Operations.FAILURE.value:
                logging.error(f"Reading message failed: {data_received['info']}")
            else:
                logging.error("Reading message failed")

            return

        except Exception as e:
            logging.error(f"Unexpected error in read_message: {e}")
            return

    def delete_messages(self, messages):
        """
        Deletes a list of messages from the server.

        Args:
            messages: List of messages to delete

        Returns:
            int: True if all messages are deleted successfully, False otherwise
        """
        # iterates through the list of messages and deletes each message
        for message in messages:
            try:
                sender = message["sender"]
                receiver = message["receiver"]
                timestamp = message["timestamp"]
                msg = message["message"]
                if not self.delete_message(sender, receiver, msg, timestamp):
                    logging.error(
                        f"message from {sender} to {receiver} on {timestamp} could not be deleted"
                    )
                    return False
            except KeyError as e:
                logging.error(f"Message is missing required field: {e}")
                return False

        return True

    def delete_message(self, sender, receiver, msg, timestamp):
        """
        Deletes a single message from the server.

        Args:
            sender: The sender of the message
            receiver: The receiver of the message
            msg: The message content
            timestamp: The timestamp of the message

        Returns:
            bool: True if the message is deleted successfully, False otherwise
        """
        data = self.create_data_object(
            self.protocol_version,
            Operations.DELETE_MESSAGE.value,
            {
                "sender": sender,
                "receiver": receiver,
                "timestamp": timestamp,
                "message": msg,
            },
        )
        # sends the data object to the server and receives the response in data_received
        data_received = self.client_send(data)
        # unwraps the data object to return the info field
        data_received = self.unwrap_data_object(data_received)
        if data_received and data_received["type"] == Operations.SUCCESS.value:
            logging.info("Deleting message successful!")
            return True

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            logging.error(f"Deleting message failed: {data_received['info']}")
        else:
            logging.error("Reading message failed")

        return False

    def delete_account(self):
        """
        Handles the account deletion process for the client application.
        Prompts the user for their username and sends the account deletion request to the server.

        Returns:
            bool: True if account deletion is successful, False otherwise
        """
        data = self.create_data_object(
            self.protocol_version,
            Operations.DELETE_ACCOUNT.value,
            {"username": self.username},
        )

        # sends the data object to the server and receives the response in data_received
        data_received = self.client_send(data)
        # unwraps the data object to return the info field
        data_received = self.unwrap_data_object(data_received)
        if data_received and data_received["type"] == Operations.SUCCESS.value:
            self.username = ""
            return True

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            logging.error(f"Deleting account failed: {data_received['info']}")
        else:
            logging.error("Deleting account failed. Try again.")

        return False

    def wire_protocol_receive(self, recv_data):
        """
        Checks the first byte of the received data to determine the protocol version and unpacks accordingly.

        Args:
            recv_data: The data to send to the server

        Returns:
            dict: The response received from the server
        """
        first_byte = recv_data[0:1].decode(self.FORMAT)
        if first_byte == Version.WIRE_PROTOCOL.value:
            return unpacking(recv_data)
        elif first_byte == Version.JSON.value:
            return json.loads(recv_data[1:].decode(self.FORMAT))
        else:
            print(f"Unknown protocol indicator: {first_byte}")
            return None

    def wire_protocol_send(self, data):
        """
        Checks the version of the data object and packs it accordingly.

        Args:
            data: The data object to send to the server
        """
        if data["version"] == Version.WIRE_PROTOCOL.value:
            return packing(data)
        else:
            json_data = json.dumps(data).encode(self.FORMAT)
            return data["version"].encode(self.FORMAT) + json_data

    def client_send(self, data):
        """
        Sends data to the server and receives a response.

        Args:
            data: The data to send to the server

        Returns:
            dict: The response received from the server
        """
        # checks to see if the client socket is connected to the server
        while True:
            if self.client_socket:
                break
        try:

            # serializes the data to be sent to the server
            serialized_data = self.wire_protocol_send(data)
            # calculates the length of the serialized data
            data_length = len(serialized_data)

            # prints the operation and length of the serialized data for experimentation
            print("--------------------------------")
            print(f"OPERATION: {OperationNames[data['type']]}")
            print(
                f"SERIALIZED DATA LENGTH: {data_length} {'WIRE PROTOCOL' if self.protocol_version == '1' else 'JSON'}"
            )
            print("--------------------------------")
            # creates the header data with the length of the serialized data
            header_data = f"{data_length:<{self.HEADER}}".encode(self.FORMAT)

            self.data.outb = serialized_data

            self.client_socket.send(header_data)
            self.client_socket.send(self.data.outb)

            # Temporarily set socket to blocking for response
            self.client_socket.setblocking(True)
            try:
                header_response = self.client_socket.recv(self.HEADER).decode(
                    self.FORMAT
                )

                if header_response:
                    message_length = int(header_response)
                    recv_data = b""
                    while len(recv_data) < message_length:
                        chunk = self.client_socket.recv(message_length - len(recv_data))
                        recv_data += chunk
                    try:
                        return self.wire_protocol_receive(recv_data)
                    except Exception as e:
                        print(f"Error decoding data: {e}")
                        return None

            finally:
                # Set back to non-blocking
                self.client_socket.setblocking(False)

        except Exception as e:
            logging.error(f"Error in sending data: {e}")
            self.cleanup(self.client_socket)
            return None

    def client_receive(self):
        """
        Receives data from the server. Specifically used to poll for incoming messages.

        Returns:
            dict: The data received from the server
        """
        try:
            # receives the header data from the server non-blcoking
            msg_length = self.client_socket.recv(self.HEADER, socket.MSG_DONTWAIT)
            if not msg_length:
                # Connection closed by server
                self.cleanup(self.client_socket)
                return None

            msg_length = msg_length.decode(self.FORMAT).strip()
            if not msg_length:
                return None

            message_length = int(msg_length)
            if message_length > 0:
                recv_data = b""
                while len(recv_data) < message_length:
                    chunk = self.client_socket.recv(message_length - len(recv_data))
                    recv_data += chunk

                if recv_data:
                    unpacked_data = self.wire_protocol_receive(recv_data)
                    # unpacked_data = unpacking(recv_data)
                    unpacked_data = self.unwrap_data_object(unpacked_data)
                    message = unpacked_data["info"]["message"]
                    if unpacked_data["type"] == Operations.DELIVER_MESSAGE_NOW.value:
                        return message
            return None

        except BlockingIOError:
            return None
        except Exception as e:
            self.cleanup(self.client_socket)
            return None

    def cleanup(self, sock):
        """Unregister and close the socket."""
        try:
            self.sel.unregister(sock)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
        self.client_socket = None
