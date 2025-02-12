from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import selectors
from tkinter import scrolledtext
from protocol_client import Client
from protocol_server import Server
import time

# Global connection ID counter
connection_id = 0


class ChatAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat App")
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(padx=20, pady=20)

        self.client = None  # Will be assigned when Client is initialized
        self.notification_windows = []
        self.unread_messages = []  # New list to store unread messages

        # Create a frame for notifications that will always be visible
        self.notification_frame = tk.Frame(root)
        self.notification_frame.pack(side="bottom", fill="x", padx=5, pady=5)

        # Add "New Messages" label
        self.messages_header = tk.Label(
            self.notification_frame,
            text="New Messages",
            font=("Arial", 10, "bold"),
            fg="white"
        )
        self.messages_header.pack(side="top", anchor="w", padx=5)

        # Create a scrolled text widget for unread messages
        self.notification_text = scrolledtext.ScrolledText(
            self.notification_frame,
            height=3,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD
        )
        self.notification_text.pack(side="left", fill="x", expand=True)  # Pack it when created

        self.start_menu()

    def clear_frame(self):
        """Clears all widgets from the main frame before switching screens."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def poll_incoming_messages(self):
        if self.client:
            try:
                with self.client.CLIENT_LOCK:
                    message = self.client.client_receive()
                    if message:
                        self.root.after(0, self.show_notification, message)
            except Exception as e:
                print(f"Error polling messages in GUI: {e}")

            # Schedule the next poll
            self.root.after(10, self.poll_incoming_messages)

    def show_notification(self, message):
        """Display a popup notification for new messages"""

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.unread_messages.append(f"[{timestamp}] {message}")
        
        # Update the notification text widget
        self.notification_text.delete(1.0, tk.END)
        for msg in self.unread_messages:
            self.notification_text.insert(tk.END, f"{msg}\n")
        
        # Auto-scroll to the bottom
        self.notification_text.see(tk.END)

        # Update the notification label
        # self.notification_label.config(
        #     text=f"New message: {message}...",
        # )

        # Create popup window
        notification = tk.Toplevel(self.root)
        notification.title("New Message")

        # Calculate position (bottom right of screen)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        notification.geometry(f"300x100+{screen_width-320}+{screen_height-120}")

        # Add message to notification window
        tk.Label(notification, text=message, wraplength=250, justify="left").pack(
            padx=10, pady=5
        )

        # Add close button
        tk.Button(notification, text="Close", command=notification.destroy).pack(pady=5)

        # Store reference to prevent garbage collection
        self.notification_windows.append(notification)

        # Remove closed windows from the list
        self.notification_windows = [
            win for win in self.notification_windows if win.winfo_exists()
        ]

    def start_menu(self):
        """Initial menu to choose between Client or Server."""
        self.notification_frame.pack_forget()
        self.clear_frame()
        tk.Label(self.main_frame, text="Select an Option", font=("Arial", 14)).pack(
            pady=10
        )
        tk.Button(
            self.main_frame, text="Client", command=self.start_client, width=20
        ).pack(pady=5)
        tk.Button(
            self.main_frame, text="Server", command=self.start_server, width=20
        ).pack(pady=5)

    def start_client(self):
        """Starts the client instance with Tkinter GUI."""
        global connection_id
        self.clear_frame()

        # Create selector and client instance
        sel = selectors.DefaultSelector()
        self.client = Client(connection_id, sel)
        connection_id += 1

        # Connect client socket and register with the SAME selector
        self.client.client_socket.connect_ex((self.client.host, self.client.port))
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.client.sel.register(self.client.client_socket, events, data=self.client.data)
        
        # Start polling in a background thread
        self.polling_active = True
        self.polling_thread = threading.Thread(
            target=self.background_poll,
            daemon=True
        )
        self.polling_thread.start()

        # # Start GUI polling for messages
        # self.root.after(1000, self.poll_incoming_messages)

        # Show login menu
        self.login_menu()

    def background_poll(self):
        """Continuously polls for messages in background thread"""
        while self.polling_active:
            try:
                if self.client.client_socket:
                    try:
                        message = self.client.client_receive()
                        if message:
                            # Schedule notification on main thread
                            self.root.after(0, self.show_notification, message)
                    except BlockingIOError:
                        # No data available, this is normal
                        pass
                time.sleep(0.01)  # Short sleep to prevent CPU spinning
            except Exception as e:
                print(f"Error in background poll: {e}")
                break

    def cleanup(self):
        """Clean up resources before closing"""
        self.polling_active = False
        if hasattr(self, 'polling_thread'):
            self.polling_thread.join(timeout=1.0)
        if self.client:
            self.client.cleanup(self.client.client_socket)

    def login_menu(self):
        """Login screen with username and password input fields."""
        self.clear_frame()

        tk.Label(self.main_frame, text="Login", font=("Arial", 14)).pack(pady=10)

        tk.Label(self.main_frame, text="Username:").pack()
        self.username_entry = tk.Entry(self.main_frame)
        self.username_entry.pack()

        tk.Label(self.main_frame, text="Password:").pack()
        self.password_entry = tk.Entry(self.main_frame, show="*")  # Hide password input
        self.password_entry.pack()

        tk.Button(
            self.main_frame, text="Login", command=self.attempt_login, width=20
        ).pack(pady=5)
        tk.Button(
            self.main_frame,
            text="Create Account",
            command=self.create_account_menu,
            width=20,
        ).pack(pady=5)
        tk.Button(
            self.main_frame,
            text="List Accounts",
            command=self.list_accounts_menu,
            width=20,
        ).pack(pady=5)
        tk.Button(self.main_frame, text="Back", command=self.start_menu, width=20).pack(
            pady=5
        )

    def attempt_login(self):
        """Gets username and password from entries and calls client.login()."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Both fields are required!")
            return

        success = self.client.login(username, password)

        if success:
            messagebox.showinfo("Success", "Login successful!")
            self.notification_frame.pack(side="bottom", fill="x", padx=5, pady=5)
            self.messages_header.pack(side="top", anchor="w", padx=5)
            self.user_menu()
        else:
            messagebox.showerror("Error", "Login failed. Try again.")

    def list_accounts_menu(self):
        """Gets search string to list accounts"""
        self.clear_frame()

        tk.Label(
            self.main_frame, text="Search for an account", font=("Arial", 14)
        ).pack(pady=10)

        tk.Label(self.main_frame, text="Username:").pack()
        self.username_search_entry = tk.Entry(self.main_frame)
        self.username_search_entry.pack()

        tk.Button(
            self.main_frame,
            text="Search Account",
            command=self.attempt_list_accounts,
            width=20,
        ).pack(pady=5)
        tk.Button(self.main_frame, text="Back", command=self.login_menu, width=20).pack(
            pady=5
        )

    def attempt_list_accounts(self):
        """Lists accounts associated under a given search string"""
        username = self.username_search_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Search string is required!")
            return

        accounts = self.client.list_accounts(username)

        if accounts is not None:
            if len(accounts) == 0:
                messagebox.showinfo("Success", "No accounts found")

            else:
                messagebox.showinfo("Success", "Searched accounts were returned")
                self.display_accounts(accounts)
        else:
            messagebox.showerror("Error", "Account search failed.")

    def display_accounts(self, accounts):
        """Lists accounts under the GUI"""
        msg_window = tk.Toplevel(self.root)
        msg_window.title("Accounts")
        msg_window.geometry("450x400")

        # Scrollable Listbox
        listbox_frame = tk.Frame(msg_window)
        listbox_frame.pack(pady=10, fill="both", expand=True)

        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
        self.listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.MULTIPLE,
            width=60,
            height=15,
            yscrollcommand=scrollbar.set,
        )

        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        for idx, acc in enumerate(accounts):
            display_text = f"{acc}"  # Show preview
            self.listbox.insert("end", display_text)

    def create_account_menu(self):
        """Account creation screen."""
        self.clear_frame()

        tk.Label(self.main_frame, text="Create Account", font=("Arial", 14)).pack(
            pady=10
        )

        tk.Label(self.main_frame, text="Username:").pack()
        self.new_username_entry = tk.Entry(self.main_frame)
        self.new_username_entry.pack()

        tk.Label(self.main_frame, text="Password:").pack()
        self.new_password_entry = tk.Entry(self.main_frame, show="*")
        self.new_password_entry.pack()

        tk.Button(
            self.main_frame,
            text="Create Account",
            command=self.attempt_create_account,
            width=20,
        ).pack(pady=5)
        tk.Button(self.main_frame, text="Back", command=self.login_menu, width=20).pack(
            pady=5
        )

    def attempt_create_account(self):
        """Gets username and password for account creation and calls client.create_account()."""
        username = self.new_username_entry.get().strip()
        password = self.new_password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Both fields are required!")
            return

        success = self.client.create_account(username, password)

        if success:
            messagebox.showinfo("Success", "Account created successfully!")
            self.login_menu()
        else:
            messagebox.showerror("Error", "Account creation failed.")

    def user_menu(self):
        """User menu after login."""
        self.clear_frame()
        tk.Label(
            self.main_frame,
            text=f"Welcome, {self.client.username}!",
            font=("Arial", 14),
        ).pack(pady=10)

        tk.Button(
            self.main_frame,
            text="Send Message",
            command=self.send_message_menu,
            width=20,
        ).pack(pady=5)
        tk.Button(
            self.main_frame, text="Read Messages", command=self.read_messages, width=20
        ).pack(pady=5)
        tk.Button(
            self.main_frame,
            text="Delete Account",
            command=self.delete_account,
            width=20,
        ).pack(pady=5)

    def send_message_menu(self):
        """Message sending screen."""
        self.clear_frame()
        tk.Label(self.main_frame, text="Send Message", font=("Arial", 14)).pack(pady=10)

        tk.Label(self.main_frame, text="Receiver:").pack()
        self.receiver_entry = tk.Entry(self.main_frame)
        self.receiver_entry.pack()

        tk.Label(self.main_frame, text="Message:").pack()
        self.message_entry = tk.Entry(self.main_frame)
        self.message_entry.pack()

        tk.Button(
            self.main_frame, text="Send", command=self.attempt_send_message, width=20
        ).pack(pady=5)
        tk.Button(self.main_frame, text="Back", command=self.user_menu, width=20).pack(
            pady=5
        )

    def attempt_send_message(self):
        """Gets receiver and message and calls client.send_message()."""
        receiver = self.receiver_entry.get().strip()
        message = self.message_entry.get().strip()

        if not receiver or not message:
            messagebox.showerror("Error", "Both fields are required!")
            return

        success = self.client.send_message(receiver, message)

        if success:
            messagebox.showinfo("Success", "Message sent successfully!")
        else:
            messagebox.showerror("Error", "Failed to send message.")

        self.user_menu()

    def read_messages(self):
        """Fetch messages and display options for reading and deleting."""
        self.unread_messages.clear()
        self.notification_text.delete(1.0, tk.END)

        messages = self.client.read_message()  # Fetch messages

        if messages is None:
            messagebox.showerror("Error", "Failed to retrieve messages.")
            return

        total_messages = len(messages)
        if total_messages == 0:
            messagebox.showinfo("Messages", "No messages.")
            return

        # Ask how many messages to read
        num_to_read = simpledialog.askinteger(
            "Messages",
            f"You have {total_messages} messages.\nHow many do you want to read?",
            minvalue=0,
            maxvalue=total_messages,
        )

        if num_to_read is None or num_to_read == 0:
            return  # User canceled input
        print(messages[-num_to_read:])
        # Create a new window for messages
        self.display_messages(messages[-num_to_read:])

    def display_messages(self, messages):
        """Display messages in a Listbox with multi-select for deletion."""
        self.msg_window = tk.Toplevel(self.root)
        self.msg_window.title("Your Messages")
        self.msg_window.geometry("450x400")

        tk.Label(
            self.msg_window,
            text="Select messages to delete:",
            font=("Arial", 12, "bold"),
        ).pack(pady=5)

        # Scrollable Listbox
        listbox_frame = tk.Frame(self.msg_window)
        listbox_frame.pack(pady=10, fill="both", expand=True)

        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
        self.listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.MULTIPLE,
            width=60,
            height=15,
            yscrollcommand=scrollbar.set,
        )

        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        # Populate listbox with messages
        self.message_map = {}  # Maps listbox index to message object
        for idx, msg in enumerate(messages):
            sender, receiver, content, timestamp = (
                msg.get("sender"),
                msg.get("receiver"),
                msg.get("message"),
                msg.get("timestamp"),
            )
            displayed_timestamp = datetime.strptime(
                timestamp, "%Y-%m-%d %H:%M:%S.%f"
            ).strftime("%Y-%m-%d")
            display_text = f"From {sender} to {receiver} on {displayed_timestamp}: {content[:50]}"  # Show preview
            self.listbox.insert("end", display_text)
            self.message_map[idx] = msg  # Store full message

        delete_button = tk.Button(
            self.msg_window, text="Delete Selected", command=self.delete_selected
        )
        delete_button.pack(pady=10)

    def delete_selected(self):
        """Deletes selected messages from the listbox."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "No messages selected for deletion.")
            return

        to_delete = [self.message_map[idx] for idx in selected_indices]
        result = self.client.delete_messages(to_delete)

        if result:
            messagebox.showinfo("Success", "Selected messages deleted successfully!")
            self.msg_window.destroy()
        else:
            messagebox.showerror("Error", "Failed to delete some messages.")

    def delete_account(self):
        """Deletes the user's account."""
        confirmation = messagebox.askyesno(
            "Delete Account", "Are you sure you want to delete your account?"
        )
        if confirmation:
            success = self.client.delete_account()
            if success:
                messagebox.showinfo("Success", "Account deleted successfully.")
                self.start_menu()
            else:
                messagebox.showerror("Error", "Account deletion failed.")

    def start_server(self):
        """Starts the server in a separate thread."""
        self.clear_frame()
        tk.Label(self.main_frame, text="Server Started", font=("Arial", 14)).pack(
            pady=10
        )
        threading.Thread(target=self.run_server, daemon=True).start()

    def run_server(self):
        """Runs the server."""
        try:
            server = Server()
            server.handle_client()

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Server Error", e))


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatAppGUI(root)
    root.mainloop()
