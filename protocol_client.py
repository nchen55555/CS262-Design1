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

    def login(self):
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        if username and password: 
            data = {
                "version": self.VERSION,
                "type": Operations.LOGIN.value,
                "info": f"username={username}&password={password}",
            }
            data_received = self.client_send(Operations.LOGIN, data)
            if data_received and data_received["type"] == Operations.SUCCESS.value: 
                print("Login successful!")
                self.user_menu()
            elif data_received and data_received["type"] == Operations.FAILURE.value: 
                print(data_received["info"])
            else: 
                raise ValueError("Login failed")
        else: 
            raise ValueError("Username and password cannot be empty")

    def create_account(self):
        print("Create Account")

    def list_accounts(self):
        print("List Accounts")

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
                header_response = self.client_socket.recv(self.HEADER).decode(self.FORMAT)
                
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
