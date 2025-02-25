from dotenv import load_dotenv
from user import User
from message import Message
from datetime import datetime

from protos import app_pb2_grpc, app_pb2
from util import hash_password


class Server(app_pb2_grpc.AppServicer):
    HEADER = 64
    FORMAT = "utf-8"

    def __init__(self):
        load_dotenv()
        # all users and their associated data stored in the User object
        self.user_login_database = {
            "michael": User("michael", hash_password("goat")),
            "nicole": User("nicole", hash_password("chen")),
        }

        self.active_users = {}

    def check_valid_user(self, username):
        """
        Checks if the user is in the login database and active users.

        username: the username of the user

        Returns:
            bool: True if the user is in the login database and active users, False otherwise
        """
        # check if the user is in the login database and active users
        return username in self.user_login_database and username in self.active_users

    def RPCLogin(self, request, context):
        """
        Logs in the user if the username and password are correct.

        Args:
            username: The username of the user
            password: The password of the user

        Returns:
            dict: A dictionary representing the data object
        """
        # check if the username and password are correct
        if len(request.info) != 2:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Login Request Invalid")

        username, password = request.info
        if (
            username in self.user_login_database
            and self.user_login_database[username].password == password
            and username not in self.active_users
        ):

            unread_messages = len(self.user_login_database[username].unread_messages) 
            self.active_users[username] = []
            response = app_pb2.Response(
                operation=app_pb2.SUCCESS, info=f"{unread_messages}"
            )
            response_size = response.ByteSize()
            print("--------------------------------")
            print(f"OPERATION: LOGIN")
            print(f"SERIALIZED DATA LENGTH: {response_size}")
            print("--------------------------------")
            return response

        else:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Login Failed")

    def RPCCreateAccount(self, request, context):
        """
        Creates an account if the username and password are not taken.

        Args:
            username: The username of the user
            password: The password of the user

        Returns:
            dict: A dictionary representing the data object
        """
        if len(request.info) != 2:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Create Account Request Invalid")

        username, password = request.info
        # check if the username is taken
        if username in self.user_login_database:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Create Account Failed")
        # check if the username and password are not empty
        elif not username or not password:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Create Account Failed")
        # create the account
        else:
            self.user_login_database[username] = User(username, password)
            response = app_pb2.Response(operation=app_pb2.SUCCESS, info="")
            response_size = response.ByteSize()
            print("--------------------------------")
            print(f"OPERATION: CREATE ACCOUNT")
            print(f"SERIALIZED DATA LENGTH: {response_size}")
            print("--------------------------------")
            return response

    def RPCListAccount(self, request, context):
        """
        Lists all accounts that start with the search string.

        search_string: The string to search for

        Returns:
            dict: A dictionary representing the data object
        """
        try:
            if len(request.info) != 1:
                return app_pb2.Response(operation=app_pb2.FAILURE, info="List Account Request Invalid")
            search_string = request.info[0]
            accounts = [
                username
                for username in self.user_login_database.keys()
                if username.startswith(search_string)
            ]
            response = app_pb2.Response(operation=app_pb2.SUCCESS, info=accounts)
            response_size = response.ByteSize()
            print("--------------------------------")
            print(f"OPERATION: LIST ACCOUNTS")
            print(f"SERIALIZED DATA LENGTH: {response_size}")
            print("--------------------------------")
            return response

        except:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="List Account Failed")

    def RPCSendMessage(self, request, context):
        """
        Sends a message to the receiver if the sender and receiver are valid users.

        Args:
            sender: The username of the sender
            receiver: The username of the receiver
            msg: The message to send

        Returns:
            dict: A dictionary representing the data object
        """
        if len(request.info) != 3:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Send Message Request Invalid")

        sender, receiver, msg = request.info
        # check if the sender is a valid user
        if sender not in self.user_login_database:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Send Message Failed")

        # check if the receiver is a valid user
        if receiver not in self.user_login_database:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Send Message Failed")

        # check if the sender and receiver are the same
        if sender == receiver:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Send Message Failed")
        # check if the message is empty
        if not msg:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Send Message Failed")

        message = Message(sender, receiver, msg)

        # check if the receiver is active and appends to unread messages if not active and regular messages otherwise
        if receiver not in self.active_users:
            self.user_login_database[receiver].unread_messages.append(message)
        else:
            self.active_users[receiver].append(message)
            self.user_login_database[receiver].messages.append(message)

        # append the message to the sender's messages
        self.user_login_database[sender].messages.append(message)
        
        response = app_pb2.Response(operation=app_pb2.SUCCESS, info="")
        response_size = response.ByteSize()
        print("--------------------------------")
        print(f"OPERATION: SEND MESSAGE")
        print(f"SERIALIZED DATA LENGTH: {response_size}")
        print("--------------------------------")
        return response
    
    
    def RPCGetInstantMessages(self, request, context):
        """
        Gets the instant messages of the user.
        """
        if len(request.info) != 1:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Get Instant Messages Request Invalid")
        
        username = request.info[0]

        if username not in self.user_login_database or username not in self.active_users:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="User not found")
                
        incoming_messages = self.active_users[username]

        incoming_messages = [
                app_pb2.Message(
                    sender=msg.sender,
                    receiver=msg.receiver,
                    timestamp=str(msg.timestamp),
                    message=msg.message,
                )
                for msg in incoming_messages
            ]
        response = app_pb2.Response(operation=app_pb2.SUCCESS, info="", messages=incoming_messages)
        return response

    def RPCReadMessage(self, request, context):
        """
        Reads the messages of the user.

        username: The username of the user

        Returns:
            dict: A dictionary representing the data object
        """
        if len(request.info) != 1:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Read Message Request Invalid")
        username = request.info[0]

        # check if the user is a valid user
        if username not in self.user_login_database:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Read Message Failed")

        try:
            user = self.user_login_database[username]
            # check if the user has unread messages and appends to messages if they do
            if user.unread_messages:
                user.messages += user.unread_messages
                user.unread_messages = []

            # sort the messages by timestamp
            messages = sorted(user.messages, key=lambda x: x.timestamp)

            # create the data object as a list of dictionaries that represent the messages
            message_list = [
                app_pb2.Message(
                    sender=msg.sender,
                    receiver=msg.receiver,
                    timestamp=str(msg.timestamp),
                    message=msg.message,
                )
                for msg in messages
            ]
            self.active_users[username] = []
            response = app_pb2.Response(
                operation=app_pb2.SUCCESS, info="", messages=message_list
            )
            response_size = response.ByteSize()
            print("--------------------------------")
            print(f"OPERATION: READ MESSAGE")
            print(f"SERIALIZED DATA LENGTH: {response_size}")
            print("--------------------------------")
            return response

        except:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Read Message Failed")

    def delete_message_from_user(
        self, user, sender, receiver, msg, timestamp, unread=False
    ):
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

    def RPCDeleteMessage(self, request, context):
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
        if len(request.info) != 4:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Delete Message Request Invalid")

        sender, receiver, msg, timestamp = request.info
        try:
            # check if the sender is a valid user
            if sender in self.user_login_database:
                user = self.user_login_database[sender]
                # gets the user and searches for the message to delete
                self.delete_message_from_user(user, sender, receiver, msg, timestamp)

            # check if the receiver is a valid user and deletes the message from their messages
            if receiver in self.user_login_database:
                user = self.user_login_database[receiver]
                self.delete_message_from_user(
                    user, sender, receiver, msg, timestamp, unread=True
                )
            response = app_pb2.Response(operation=app_pb2.SUCCESS, info="")
            response_size = response.ByteSize()
            print("--------------------------------")
            print(f"OPERATION: DELETE MESSAGE")
            print(f"SERIALIZED DATA LENGTH: {response_size}")
            print("--------------------------------")
            return response

        except:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Delete Message Failed")

    def RPCDeleteAccount(self, request, context):
        """
        Deletes an account from the user login database and active users.

        Args:
            username: The username of the user

        Returns:
            dict: A dictionary representing the data object
        """
        if len(request.info) != 1:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Delete Account Request Invalid")

        username = request.info[0]
        try:
            # check if the user is a valid user
            if username not in self.user_login_database:
                return app_pb2.Response(operation=app_pb2.FAILURE, info="Delete Account Failed")

            self.user_login_database.pop(username)
            if username in self.active_users:
                self.active_users.pop(username)
            response = app_pb2.Response(operation=app_pb2.SUCCESS, info="")
            response_size = response.ByteSize()
            print("--------------------------------")
            print(f"OPERATION: DELETE ACCOUNT")
            print(f"SERIALIZED DATA LENGTH: {response_size}")
            print("--------------------------------")
            return response

        except:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Delete Account Failed")
        
    def RPCLogout(self, request, context):
        """
        Logs out the user.
        """
        if len(request.info) != 1:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Logout Request Invalid")
        
        username = request.info[0]
        try:
            self.active_users.pop(username)
            response = app_pb2.Response(operation=app_pb2.SUCCESS, info="")
            response_size = response.ByteSize()
            print("--------------------------------")
            print(f"OPERATION: LOGOUT")
            print(f"SERIALIZED DATA LENGTH: {response_size}")
            print("--------------------------------")
            return response
        except:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="Logout Failed")
