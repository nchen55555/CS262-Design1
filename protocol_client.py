import socket
import selectors
import types
from consolemenu import *
from consolemenu.items import *
from dotenv import load_dotenv
import os
from wire_protocol import packing, unpacking
from operations import OperationNames, Operations
import time
from util import hash_password, list_accounts_menu, message_browser
import curses
import pwinput
import threading
import time
import logging


class Client:
    VERSION = "2"
    FORMAT = "utf-8"
    HEADER = 64

    def __init__(self, conn_id, sel):
        self.host = os.getenv("HOST")
        self.port = int(os.getenv("PORT"))
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setblocking(False)
        self.conn_id = conn_id
        self.data = types.SimpleNamespace(connid=self.conn_id, outb=b"")
        self.sel = sel
        self.current_session = {"username": ""}
        self.polling_thread = threading.Event()
        self.client_lock = threading.Lock()

    def show_menu(self, options_list):
        selection_menu = SelectionMenu(
            options_list, "Select an option", show_exit_option=False
        )

        selection_menu.show()
        selection_menu.join()
        selection = selection_menu.selected_option
        return options_list[selection]

    def start_page(self):
        os.system("clear")
        options_list = [
            OperationNames.LOGIN.value,
            OperationNames.CREATE_ACCOUNT.value,
            OperationNames.LIST_ACCOUNTS.value,
            OperationNames.EXIT.value,
        ]
        selection = self.show_menu(options_list)
        match selection:
            case OperationNames.LOGIN.value:
                self.login()
            case OperationNames.CREATE_ACCOUNT.value:
                self.create_account()
            case OperationNames.LIST_ACCOUNTS.value:
                self.list_accounts()
            case OperationNames.EXIT.value:
                self.client_socket.close()
                return

    def user_menu(self):
        """Handles user interactions while polling for unread messages."""

        options_list = [
            OperationNames.SEND_MESSAGE.value,
            OperationNames.READ_MESSAGE.value,
            OperationNames.DELETE_ACCOUNT.value,
            OperationNames.EXIT.value,
        ]

        while True:  # Keep showing the menu until the user exits
            selection = self.show_menu(options_list)

            match selection:
                case OperationNames.SEND_MESSAGE.value:
                    self.send_message()
                case OperationNames.READ_MESSAGE.value:
                    self.read_message()
                case OperationNames.DELETE_ACCOUNT.value:
                    self.delete_account()
                case OperationNames.EXIT.value:
                    self.client_socket.close()
                    return

    def display_msgs(self, messages):
        _, deleted_messages = curses.wrapper(message_browser, messages)
        return deleted_messages

    def login(self):
        username = input("Enter username: ").strip()
        password = pwinput.pwinput(prompt="Enter password: ").strip()
        password = hash_password(password)
        data = {
            "version": self.VERSION,
            "type": Operations.LOGIN.value,
            "info": f"username={username}&password={password}",
        }
        data_received = self.client_send(Operations.LOGIN, data)
        if data_received and data_received["type"] == Operations.SUCCESS.value:
            print("Login successful!")
            self.current_session["username"] = username
            self.user_menu()
            return

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            print(data_received["info"])
        else:
            print("Login Failed")

        time.sleep(1)
        self.start_page()

    def create_account(self):
        username = ""
        password = ""
        while not username or not password:
            username = input("Enter a unique username: ").strip()
            password = input("Enter a password: ").strip()

            if "," in username or "&" in username:
                print("Cannot have , or & in username")
                username = ""

        data = {
            "version": self.VERSION,
            "type": Operations.CREATE_ACCOUNT.value,
            "info": f"username={username}&password={password}",
        }
        data_received = self.client_send(Operations.CREATE_ACCOUNT, data)
        if data_received and data_received["type"] == Operations.SUCCESS.value:
            print("Creation of account successful!")
            self.current_session["username"] = username
            self.user_menu()
            return

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            print(data_received["info"])
        else:
            print("Account creation failed")

        time.sleep(1)
        self.start_page()

    def list_accounts(self):
        print("List Accounts")
        search_string = input("Search for a particular account: ").strip()
        data = {
            "version": self.VERSION,
            "type": Operations.LIST_ACCOUNTS.value,
            "info": search_string,
        }
        data_received = self.client_send(Operations.LIST_ACCOUNTS, data)
        if data_received and data_received["type"] == Operations.SUCCESS.value:
            print("Listing of accounts successful!")
            accounts = data_received["info"].split(", ")
            if accounts and accounts != [""]:
                curses.wrapper(list_accounts_menu, accounts)
            else:
                print("No accounts found.")

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            print(data_received["info"])
        else:
            print("Listing accounts failed")

        time.sleep(1)
        self.start_page()

    def send_message(self):
        print("Sending message to someone else")
        receiver = input(
            "Type the username of the person you want to send a message to.\n"
        )
        msg = input("Type what you want to say.\n")
        data = {
            "version": self.VERSION,
            "type": Operations.SEND_MESSAGE.value,
            "info": f"sender={self.current_session['username']}&receiver={receiver}&msg={msg}",
        }

        data_received = self.client_send(Operations.SEND_MESSAGE, data)
        if data_received and data_received["type"] == Operations.SUCCESS.value:
            print("Sending message successful!")
            print(data_received["info"])

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            print(data_received["info"])
        else:
            print("Sending message failed")

        time.sleep(1)
        self.user_menu()

    def read_message(self):
        print("Reading message")
        try:
            data = {
                "version": self.VERSION,
                "type": Operations.READ_MESSAGE.value,
                "info": f"{self.current_session['username']}",
            }

            data_received = self.client_send(Operations.READ_MESSAGE, data)
            if data_received and data_received["type"] == Operations.SUCCESS.value:
                print("Reading message successful!")
                messages = (
                    data_received["info"].split("\n") if data_received["info"] else []
                )
                print("Total Messages: ", len(messages))
                num_of_messages = 0
                while True and len(messages) > 0:
                    try:
                        num_of_messages = int(
                            input("How many messages do you want to read? ")
                        )
                        if num_of_messages > len(messages):
                            print("Please enter a valid integer number")
                        else:
                            break
                    except ValueError:
                        print("Please enter a valid integer number")
                if num_of_messages > 0:
                    deleted_msgs = self.display_msgs(messages[-num_of_messages:])
                    print("deleted_msgs: ", deleted_msgs)
                    if deleted_msgs:
                        if self.delete_messages(deleted_msgs) == 0:
                            print("Deleted messages successful!")

                        else:
                            print("Deleted messages failed")

            elif data_received and data_received["type"] == Operations.FAILURE.value:
                print(data_received["info"])
            else:
                print("Reading message failed")

            time.sleep(1)
            self.user_menu()

        except:
            print("Something failed")
            time.sleep(1)
            self.user_menu()

    def delete_messages(self, messages):
        for message in messages:
            sender, receiver, timestamp, msg = message.split(",", maxsplit=3)
            if self.delete_message(sender, receiver, msg, timestamp) != 0:
                print(
                    f"message from {sender} to {receiver} on {timestamp} could not be deleted"
                )
                return 1

        return 0

    def delete_message(self, sender, receiver, msg, timestamp):
        print("Deleting Message")
        data = {
            "version": self.VERSION,
            "type": Operations.DELETE_MESSAGE.value,
            "info": f"sender={sender}&receiver={receiver}&msg={msg}&timestamp={timestamp}",
        }

        data_received = self.client_send(Operations.DELETE_MESSAGE, data)
        if data_received and data_received["type"] == Operations.SUCCESS.value:
            print("Deleting message successful!")
            return 0

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            print(data_received["info"])
        else:
            print("Reading message failed")

        return 1

    def delete_account(self):
        print("Deleting Account")
        data = {
            "version": self.VERSION,
            "type": Operations.DELETE_ACCOUNT.value,
            "info": f"{self.current_session['username']}",
        }
        username = input("Type in your username if you want to delete your account: ")
        if username != self.current_session["username"]:
            self.user_menu()

        data_received = self.client_send(Operations.DELETE_ACCOUNT, data)
        print("data: ", data_received)
        if data_received and data_received["type"] == Operations.SUCCESS.value:
            print("Deleting account successful!")
            print(data_received["info"])
            self.start_page()

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            print(data_received["info"])
        else:
            print("Deleting account failed")

        time.sleep(1)
        self.user_menu()

    def client_send(self, operation, data):
        while True:
            if self.client_socket:
                break
        try:
            serialized_data = packing(data)
            data_length = len(serialized_data)
            header_data = f"{data_length:<{self.HEADER}}".encode(self.FORMAT)
            self.data.outb = serialized_data

            self.client_socket.sendall(header_data)
            self.client_socket.sendall(self.data.outb)

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
                    return unpacking(recv_data)

            finally:
                # Set back to non-blocking
                self.client_socket.setblocking(False)

        except Exception as e:
            print(f"Error in client_send: {e}")
            self.cleanup(self.client_socket)
            return None

    def client_receive(self):
        try:
            msg_length = self.client_socket.recv(self.HEADER, socket.MSG_DONTWAIT)
            if not msg_length:
                # Connection closed by server
                self.polling_thread.clear()
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
                    message = unpacking(recv_data)
                    if message["type"] == Operations.DELIVER_MESSAGE_NOW.value:
                        return message
            return None

        except BlockingIOError:
            # No data available right now
            return None
        except Exception as e:
            logging.exception(f"Error in client_receive: {e}")
            self.polling_thread.clear()
            self.cleanup(self.client_socket)
            return None

    def cleanup(self, sock):
        """Unregister and close the socket."""
        self.polling_thread.clear()  # Stop the polling thread
        try:
            self.sel.unregister(sock)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
        self.client_socket = None

    def poll_incoming_messages(self, polling_thread):
        while polling_thread.is_set():
            try:
                with self.client_lock:
                    message = self.client_receive()
                    if message:
                        print("\r\n{}".format(message["info"]))

                time.sleep(1)

            except Exception as e:
                print(f"Error in poll_incoming_messages: {e}")
                polling_thread.set()

    def start_polling(self):
        self.polling_thread.set()
        polling_thread = threading.Thread(
            target=self.poll_incoming_messages,
            args=(self.polling_thread,),  # Fix: Add comma to make it a tuple
        )
        polling_thread.daemon = (
            True  # Make thread daemon so it exits when main thread exits
        )
        polling_thread.start()
