from dotenv import load_dotenv
from user import User
from message import Message
from datetime import datetime

from protos import app_pb2_grpc, app_pb2


class Server(app_pb2_grpc.AppServicer):
    HEADER = 64
    FORMAT = "utf-8"

    def __init__(self):
        load_dotenv()
        # all users and their associated data stored in the User object
        self.user_login_database = {"michael": User("michael", "goat")}

        # all active users and their sockets
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
            return app_pb2.Response(operation=app_pb2.FAILURE, info="")

        username, password = request.info

        if (
            username in self.user_login_database
            and self.user_login_database[username].password == password
            and username not in self.active_users
        ):
            unread_messages = len(self.user_login_database[username].unread_messages)
            return app_pb2.Response(
                operation=app_pb2.SUCCESS, info=f"{unread_messages}"
            )
        else:
            return app_pb2.Response(operation=app_pb2.FAILURE, info="")

    # def RPCCreateAccount(self, request, context):
    #     """
    #     Creates an account if the username and password are not taken.

    #     Args:
    #         username: The username of the user
    #         password: The password of the user

    #     Returns:
    #         dict: A dictionary representing the data object
    #     """
    #     # check if the username is taken
    #     if username in self.user_login_database:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": "username is taken"},
    #         )
    #     # check if the username and password are not empty
    #     elif not username or not password:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": "must supply username and password"},
    #         )
    #     # create the account
    #     else:
    #         self.user_login_database[username] = User(username, password)
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.SUCCESS.value,
    #             {"message": "Account created"},
    #         )

    # def RPCListAccount(self, request, context):
    #     """
    #     Lists all accounts that start with the search string.

    #     search_string: The string to search for

    #     Returns:
    #         dict: A dictionary representing the data object
    #     """
    #     try:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.SUCCESS.value,
    #             [
    #                 {"username": username}
    #                 for username in self.user_login_database.keys()
    #                 if username.startswith(search_string)
    #             ],
    #         )

    #     except:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": "Listing accounts failed"},
    #         )

    # def RPCSendMessage(self, request, context):
    #     """
    #     Sends a message to the receiver if the sender and receiver are valid users.

    #     Args:
    #         sender: The username of the sender
    #         receiver: The username of the receiver
    #         msg: The message to send

    #     Returns:
    #         dict: A dictionary representing the data object
    #     """
    #     # check if the sender is a valid user
    #     if sender not in self.user_login_database:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": f"{sender} is not a valid user"},
    #         )

    #     # check if the receiver is a valid user
    #     if receiver not in self.user_login_database:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": f"{receiver} is not a valid user"},
    #         )

    #     # check if the sender and receiver are the same
    #     if sender == receiver:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": "Cannot send a message to yourself"},
    #         )
    #     # check if the message is empty
    #     if not msg:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": "message is empty"},
    #         )

    #     message = Message(sender, receiver, msg)

    #     # check if the receiver is active and appends to unread messages if not active and regular messages otherwise
    #     if receiver not in self.active_users:
    #         self.user_login_database[receiver].unread_messages.append(message)
    #     else:
    #         self.user_login_database[receiver].messages.append(message)

    #     # append the message to the sender's messages
    #     self.user_login_database[sender].messages.append(message)

    #     return self.create_data_object(
    #         self.protocol_version,
    #         Operations.SUCCESS.value,
    #         {"message": f"message from {sender} has been sent to {receiver}"},
    #     )

    # def RPCReadMessage(self, request, context):
    #     """
    #     Reads the messages of the user.

    #     username: The username of the user

    #     Returns:
    #         dict: A dictionary representing the data object
    #     """
    #     # check if the user is a valid user
    #     if username not in self.user_login_database:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": f"{username} is not a valid user"},
    #         )

    #     try:
    #         user = self.user_login_database[username]
    #         # check if the user has unread messages and appends to messages if they do
    #         if user.unread_messages:
    #             user.messages += user.unread_messages
    #             user.unread_messages = []

    #         # sort the messages by timestamp
    #         messages = sorted(user.messages, key=lambda x: x.timestamp)

    #         # create the data object as a list of dictionaries that represent the messages
    #         data = [
    #             {
    #                 "sender": msg.sender,
    #                 "receiver": msg.receiver,
    #                 "timestamp": str(msg.timestamp),
    #                 "message": msg.message,
    #             }
    #             for msg in messages
    #         ]
    #         return self.create_data_object(
    #             self.protocol_version, Operations.SUCCESS.value, data
    #         )

    #     except:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": "Read message failed"},
    #         )

    # def delete_message_from_user(
    #     self, user, sender, receiver, msg, timestamp, unread=False
    # ):
    #     """
    #     Deletes a message from the user's messages and unread messages.

    #     Args:
    #         user: The user object
    #         sender: The username of the sender
    #         receiver: The username of the receiver
    #         msg: The message to delete
    #         timestamp: The timestamp of the message

    #     Returns:
    #         list: A list of messages filtered out of the deleted message
    #     """
    #     # checks to see if unread messages should also be deleted from the receiver side
    #     if unread:
    #         user.unread_messages = [
    #             message
    #             for message in user.unread_messages
    #             if not (
    #                 message.receiver == receiver
    #                 and message.sender == sender
    #                 and message.message == msg
    #                 and message.timestamp
    #                 == datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
    #             )
    #         ]
    #     user.messages = [
    #         message
    #         for message in user.messages
    #         if not (
    #             message.receiver == receiver
    #             and message.sender == sender
    #             and message.message == msg
    #             and message.timestamp
    #             == datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
    #         )
    #     ]

    # def RPCDeleteMessage(self, request, context):
    #     """
    #     Deletes a message from the user's messages and unread messages.

    #     Args:
    #         sender: The username of the sender
    #         receiver: The username of the receiver
    #         msg: The message to delete
    #         timestamp: The timestamp of the message

    #     Returns:
    #         dict: A dictionary representing the data object
    #     """
    #     try:
    #         # check if the sender is a valid user
    #         if sender in self.user_login_database:
    #             user = self.user_login_database[sender]
    #             # gets the user and searches for the message to delete
    #             self.delete_message_from_user(user, sender, receiver, msg, timestamp)

    #         # check if the receiver is a valid user and deletes the message from their messages
    #         if receiver in self.user_login_database:
    #             user = self.user_login_database[receiver]
    #             self.delete_message_from_user(
    #                 user, sender, receiver, msg, timestamp, unread=True
    #             )

    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.SUCCESS.value,
    #             {"message": "deleted message successfully"},
    #         )

    #     except:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": "Delete message failed"},
    #         )

    # def RPCDeleteAccount(self, request, context):
    #     """
    #     Deletes an account from the user login database and active users.

    #     Args:
    #         username: The username of the user

    #     Returns:
    #         dict: A dictionary representing the data object
    #     """
    #     # check if the user is a valid user
    #     if username not in self.user_login_database:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": f"{username} is not a valid user"},
    #         )

    #     try:
    #         # deletes the user from the user login database and active users
    #         self.user_login_database.pop(username)
    #         if username in self.active_users:
    #             self.active_users.pop(username)
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.SUCCESS.value,
    #             {"message": "Deletion successful"},
    #         )

    #     except:
    #         return self.create_data_object(
    #             self.protocol_version,
    #             Operations.FAILURE.value,
    #             {"message": "Deletion of account unsuccessful"},
    #         )
