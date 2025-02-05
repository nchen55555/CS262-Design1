import sys
from protocol_client import Client
from protocol_server import Server
import selectors
import types
from consolemenu import *
from consolemenu.items import *

# Global connection ID counter
connection_id = 0

if __name__ == "__main__":
    menu_list = ["Client", "Server"]
    selection_menu = SelectionMenu(menu_list,"Select an option", show_exit_option=False)
    selection_menu.show()
    selection_menu.join()

    selection = selection_menu.selected_option

    if selection == 0:
        sel = selectors.DefaultSelector()
        client = Client(connection_id, sel)
        connection_id += 1
        client.client_socket.connect_ex((client.host, client.port))
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        sel.register(client.client_socket, events, data=client.data)
        client.start_page()
    elif selection == 1:
        server = Server()
        server.handle_client()
