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


class Client:
    VERSION = "1"
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
        ]
        selection = self.show_menu(options_list)
        match selection:
            case OperationNames.LOGIN.value:
                print("recieved")
                self.login()
            case OperationNames.CREATE_ACCOUNT.value:
                self.create_account()
            case OperationNames.LIST_ACCOUNTS.value:
                self.list_accounts()

    def user_menu(self):
        print("NICE")
        options_list = [
            OperationNames.SEND_MESSAGE.value,
            OperationNames.READ_MESSAGE.value,
            OperationNames.DELETE_MESSAGE.value,
            OperationNames.DELETE_ACCOUNT.value,
        ]
        selection = self.show_menu(options_list)
        match selection:
            case OperationNames.SEND_MESSAGE.value:
                self.send_message()
            case OperationNames.READ_MESSAGE.value:
                self.read_message()
            case OperationNames.DELETE_MESSAGE.value:
                self.list_accounts()
            case OperationNames.DELETE_ACCOUNT.value:
                self.list_accounts()

    def login(self):
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
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
            print(data_received["info"])
            input("Press enter to go back")

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
        data = {
            "version": self.VERSION,
            "type": Operations.READ_MESSAGE.value,
            "info": f"{self.current_session['username']}",
        }

        data_received = self.client_send(Operations.READ_MESSAGE, data)
        print("data: ", data_received)
        if data_received and data_received["type"] == Operations.SUCCESS.value:
            print("Reading message successful!")
            print(data_received["info"])
            input("Press enter to exit")

        elif data_received and data_received["type"] == Operations.FAILURE.value:
            print(data_received["info"])
        else:
            print("Reading message failed")

        time.sleep(1)
        self.user_menu()

    def client_send(self, operation, data):
        try:
            serialized_data = packing(data)
            data_length = len(serialized_data)
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
                    response_data = self.client_socket.recv(message_length)
                    return unpacking(response_data)

            finally:
                # Set back to non-blocking
                self.client_socket.setblocking(False)

        except Exception as e:
            print(f"Error in client_send: {e}")
            self.cleanup(self.client_socket)
            return None

    def client_receive(self):
        try:
            # Temporarily set socket to blocking for receive
            self.client_socket.setblocking(True)
            try:
                recv_data = self.client_socket.recv(1024)
                if not recv_data:
                    self.cleanup(self.client_socket)
                    return
            finally:
                # Set back to non-blocking
                self.client_socket.setblocking(False)

        except ConnectionResetError:
            print(f"Client {self.data.conn_id}: Connection reset by server")
            self.cleanup(self.client_socket)
            return

    def cleanup(self, sock):
        """Unregister and close the socket."""
        try:
            self.sel.unregister(sock)
        except Exception:
            pass
        sock.close()
        self.client_socket = None
