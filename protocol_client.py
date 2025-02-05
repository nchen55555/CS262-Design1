import socket
import selectors
import types
from consolemenu import *
from consolemenu.items import *
from dotenv import load_dotenv
import os
from wire_protocol import packing, unpacking
from operations import OperationNames, Operations


class Client:

    def __init__(self, conn_id, sel):
        self.host = os.getenv("HOST")
        self.port = int(os.getenv("PORT"))
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setblocking(False)
        self.conn_id = conn_id
        self.data = types.SimpleNamespace(connid=self.conn_id, outb=b"")
        self.sel = sel

    def show_menu(self, options_list): 
        selection_menu = SelectionMenu(options_list, "Select an option", show_exit_option=False)
        selection_menu.show()
        selection_menu.join()
        selection = selection_menu.selected_option
        return selection

    def start_page(self): 
        os.system("clear")
        options_list = [OperationNames.LOGIN.value, OperationNames.CREATE_ACCOUNT.value, OperationNames.LIST_ACCOUNTS.value]
        selection = self.show_menu(options_list)
        match selection: 
            case OperationNames.LOGIN.value:
                print("recieved")
                self.login()
            case OperationNames.CREATE_ACCOUNT.value: 
                self.create_account()
            case OperationNames.LIST_ACCOUNTS.value: 
                self.list_accounts()
    
    def login(self): 
        username = ""
        password = ""
        while not username or not password:
            username = input("Enter username: ").strip()
            if not username:
                print("Username cannot be empty")
                continue
            password = input("Enter password: ").strip()
            if not password:
                print("Password cannot be empty")
                continue
        
        data = {"version": "1", "type": Operations.LOGIN, "username": username, "password": password}
        packed_data = packing(data)
        self.client_send(Operations.LOGIN, packed_data)

    def create_account(self): 
        print("Create Account")

    def list_accounts(self): 
        print("List Accounts")
    

    # TODO: #1 create client functions send message, login, delete account, etc. - follows format here
    def send_message(self, message):
        """Send a custom message to the server."""
        data = self.sel.get_key(self.sock).data
        data.outb = message.encode()
        self.sel.modify(
            self.sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data
        )

    def client_send(self, operation, data): 
        if operation == Operations.LOGIN:
            self.data.outb = packing(data)
            self.sel.modify(self.sock, selectors.EVENT_READ, data=data)
        elif operation == "register":
            self.data.outb = packing(data)
        elif operation == "delete":
            self.data.outb = packing(data)
        else:
            self.data.outb = packing(data)

        try:
            print("client sent message")
            sent = self.client_socket.send(self.data.outb)
            print(
                f"Client {data.conn_id}: Sent message: {self.data.outb.decode()}"
            )
            self.data.outb = self.data.outb[sent:]
        except BrokenPipeError:
            print(f"Client {self.conn_id}: Server closed connection")
            self.cleanup(self.client_socket)
            return

    def client_receive(self):
        try:
            recv_data = self.client_socket.recv(1024)
            if recv_data:
                print(
                    f"Client {self.conn_id}: Received: {recv_data.decode()}"
                )
            else:
                print(f"Client {self.conn_id}: Server closed connection")
                self.cleanup(self.client_socket)
                return
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
        self.sock = None

    # def handle_client_io(self):
    #     """Handle sending and receiving messages for this client."""
    #     while self.sock:
    #         # ait for activity
    #         events = self.sel.select(timeout=1)
    #         if not events:
    #             continue

    #         for key, mask in events:
    #             sock = key.fileobj
    #             data = key.data

    #             if mask & selectors.EVENT_WRITE and data.outb:
    #                 try:
    #                     sent = sock.send(data.outb)
    #                     print(
    #                         f"Client {data.conn_id}: Sent message: {data.outb.decode()}"
    #                     )
    #                     data.outb = data.outb[sent:]
    #                 except BrokenPipeError:
    #                     print(f"Client {data.conn_id}: Server closed connection")
    #                     self.cleanup(sock)
    #                     return

    #             if mask & selectors.EVENT_READ:
    #                 try:
    #                     recv_data = sock.recv(1024)
    #                     if recv_data:
    #                         print(
    #                             f"Client {data.conn_id}: Received: {recv_data.decode()}"
    #                         )
    #                     else:
    #                         print(f"Client {data.conn_id}: Server closed connection")
    #                         self.cleanup(sock)
    #                         return
    #                 except ConnectionResetError:
    #                     print(f"Client {data.conn_id}: Connection reset by server")
    #                     self.cleanup(sock)
    #                     return

    # def start(self):
    #     """Initialize client and run the event loop."""
    #     sock, data = self.start_connection()
    #     if sock is None:
    #         print(f"Client {self.conn_id}: Could not connect to server.")
    #         return

    #     self.sock = sock

    #     # start the IO handler in a separate thread
    #     io_thread = threading.Thread(target=self.handle_client_io, daemon=True)
    #     io_thread.start()

    #     # keep main thread alive
    #     while self.sock:
    #         try:
    #             message = input(f"Client {self.conn_id} > ")
    #             if message.lower() == "exit":
    #                 print(f"Client {self.conn_id}: Exiting.")
    #                 self.cleanup(self.sock)
    #                 break
    #             self.send_message(message)
    #         except KeyboardInterrupt:
    #             print(f"\nClient {self.conn_id}: Interrupted. Exiting.")
    #             self.cleanup(self.sock)
    #             break
