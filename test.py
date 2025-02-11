import unittest
import threading
import time
import socket
import selectors
import tkinter as tk
from unittest.mock import patch, MagicMock
from app import ChatAppGUI
from protocol_client import Client
from protocol_server import Server


class TestChatIntegrationWithFailures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up server and required components once for all tests"""

        # Patch tkinter.messagebox to disable popups
        cls.patcher_info = patch("tkinter.messagebox.showinfo", MagicMock())
        cls.patcher_error = patch("tkinter.messagebox.showerror", MagicMock())
        cls.patcher_yesno = patch(
            "tkinter.messagebox.askyesno", MagicMock(return_value=False)
        )
        cls.patcher_askinteger = patch(
            "tkinter.simpledialog.askinteger", MagicMock(return_value=None)
        )

        cls.patcher_info.start()
        cls.patcher_error.start()
        cls.patcher_yesno.start()
        cls.patcher_askinteger.start()

        try:
            # Start server in a separate thread
            cls.server = Server()
            cls.server_thread = threading.Thread(
                target=cls.server.handle_client, daemon=True
            )
            cls.server_thread.start()
            time.sleep(1)  # Give server time to start

            # Initialize GUI but prevent it from showing
            cls.root = tk.Tk()
            cls.root.withdraw()  # Hide the Tkinter window
            cls.app = ChatAppGUI(cls.root)

            # Create a test account
            cls.test_username = "test_user"
            cls.test_password = "test_pass"

            cls.app.start_client()
            time.sleep(1)

            cls.app.create_account_menu()
            cls.app.new_username_entry.insert(0, cls.test_username)
            cls.app.new_password_entry.insert(0, cls.test_password)
            cls.app.attempt_create_account()
        except Exception as e:
            print(f"Setup failed: {e}")

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests are done"""
        cls.patcher_info.stop()
        cls.patcher_error.stop()
        cls.patcher_yesno.stop()
        cls.patcher_askinteger.stop()

        if cls.app.client:
            cls.app.client.client_socket.close()
        cls.root.destroy()

    def setUp(self):
        """Set up before each test - log in with test account"""
        try:
            self.app.login_menu()
            self.app.username_entry.insert(0, self.test_username)
            self.app.password_entry.insert(0, self.test_password)
            self.app.attempt_login()
            time.sleep(0.5)
        except Exception as e:
            print(f"Setup failed: {e}")

    def tearDown(self):
        """Clean up after each test"""
        self.app.clear_frame()

    # Failure Tests
    def test_01_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        with self.subTest("Attempt login with wrong credentials"):
            try:
                self.app.login_menu()
                self.app.username_entry.insert(0, "wrong_user")
                self.app.password_entry.insert(0, "wrong_pass")
                result = self.app.attempt_login()
                self.assertFalse(result, "Expected login to fail, but it succeeded.")
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_02_create_duplicate_account(self):
        """Test creating account with existing username"""
        with self.subTest("Attempt to create duplicate account"):
            try:
                self.app.create_account_menu()
                self.app.new_username_entry.insert(
                    0, self.test_username
                )  # Already exists
                self.app.new_password_entry.insert(0, "new_pass")
                result = self.app.attempt_create_account()
                self.assertFalse(
                    result, "Expected account creation to fail, but it succeeded."
                )
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_03_send_message_to_nonexistent_user(self):
        """Test sending message to non-existent user"""
        with self.subTest("Attempt to send message to a nonexistent user"):
            try:
                self.app.send_message_menu()
                self.app.receiver_entry.insert(0, "nonexistent_user")
                self.app.message_entry.insert(0, "Test message")
                result = self.app.attempt_send_message()
                self.assertFalse(
                    result, "Expected message sending to fail, but it succeeded."
                )
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_04_empty_message_send(self):
        """Test sending empty message"""
        with self.subTest("Attempt to send empty message"):
            try:
                self.app.send_message_menu()
                self.app.receiver_entry.insert(0, "test_user")
                self.app.message_entry.insert(0, "")  # Empty message
                result = self.app.attempt_send_message()
                self.assertFalse(
                    result, "Expected empty message to fail, but it succeeded."
                )
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_05_server_connection_failure(self):
        """Test handling of server connection failure"""
        with self.subTest("Attempt connection to an invalid port"):
            try:
                sel = selectors.DefaultSelector()
                client = Client(99, sel)
                client.port = 9999  # Invalid port
                result = client.client_socket.connect_ex((client.host, client.port))
                self.assertNotEqual(
                    result, 0, "Expected connection failure, but it succeeded."
                )
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_06_login_empty_fields(self):
        """Test login with empty fields"""
        with self.subTest("Attempt login with empty fields"):
            try:
                self.app.login_menu()
                self.app.username_entry.insert(0, "")
                self.app.password_entry.insert(0, "")
                result = self.app.attempt_login()
                self.assertFalse(
                    result, "Expected empty login to fail, but it succeeded."
                )
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    # Success cases
    def test_01_account_creation_and_login(self):
        """Test account creation and login flow"""
        with self.subTest("Create account and log in"):
            try:
                # Create new test account
                test_user = "test_user2"
                test_pass = "test_pass2"

                self.app.create_account_menu()
                self.app.new_username_entry.insert(0, test_user)
                self.app.new_password_entry.insert(0, test_pass)
                result = self.app.attempt_create_account()

                # Try logging in with new account
                self.app.login_menu()
                self.app.username_entry.insert(0, test_user)
                self.app.password_entry.insert(0, test_pass)
                login_result = self.app.attempt_login()

                # Verify login was successful by checking if we're in user menu
                children = self.app.main_frame.winfo_children()
                labels = [w for w in children if isinstance(w, tk.Label)]
                self.assertTrue(
                    any(
                        f"Welcome, {test_user}" in label.cget("text")
                        for label in labels
                    )
                )

            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_02_message_sending_and_receiving(self):
        """Test sending and receiving messages between clients"""
        with self.subTest("Send and receive messages"):
            try:
                sel = selectors.DefaultSelector()
                client2 = Client(2, sel)
                client2.client_socket.connect_ex((client2.host, client2.port))
                events = selectors.EVENT_READ | selectors.EVENT_WRITE
                sel.register(client2.client_socket, events, data=client2.data)
                client2.start_polling()
                client2.create_account("test_user3", "test_pass3")
                client2.login("test_user3", "test_pass3")

                test_message = "Hello from test!"
                self.app.send_message_menu()
                self.app.receiver_entry.insert(0, "test_user3")
                self.app.message_entry.insert(0, test_message)
                self.app.attempt_send_message()

                time.sleep(3)
                messages = client2.read_message()
                self.assertTrue(any(msg["message"] == test_message for msg in messages))

                client2.client_socket.close()
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_03_message_deletion(self):
        """Test message deletion functionality"""
        with self.subTest("Delete a message"):
            try:
                self.app.send_message_menu()
                self.app.receiver_entry.insert(0, self.test_username)
                self.app.message_entry.insert(0, "Test message for deletion")
                self.app.attempt_send_message()

                time.sleep(1)

                self.app.read_messages()
                time.sleep(0.5)

                listbox = self.app.main_frame.listbox

                listbox.select_set("end")
                self.app.delete_selected()

                messages = self.app.client.read_message()
                self.assertFalse(
                    any(
                        msg["message"] == "Test message for deletion"
                        for msg in messages
                    )
                )

            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_04_account_listing(self):
        """Test account listing functionality"""
        with self.subTest("List accounts"):
            try:
                self.app.list_accounts_menu()
                self.app.username_search_entry.insert(0, "test_user")
                self.app.attempt_list_accounts()

                accounts = self.app.client.list_accounts("test_user")
                self.assertTrue(any(self.test_username in acc for acc in accounts))
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_05_notification_system(self):
        """Test that notifications appear when messages are received"""
        with self.subTest("Receive message notification"):
            try:
                sel2 = selectors.DefaultSelector()
                client2 = Client(3, sel2)
                client2.client_socket.connect_ex((client2.host, client2.port))
                events = selectors.EVENT_READ | selectors.EVENT_WRITE
                sel2.register(client2.client_socket, events, data=client2.data)
                client2.start_polling()
                client2.create_account("test_user4", "test_pass4")
                client2.login("test_user4", "test_pass4")
                result = client2.send_message(
                    self.test_username, "Test notification message"
                )
                print("Sent message true?", result)

                time.sleep(2)

                print("Notification Windows:", self.app.notification_windows)

                self.assertGreater(
                    len(self.app.notification_windows), 0, "No notifications appeared"
                )

                client2.client_socket.close()
            except Exception as e:
                self.fail(f"Unexpected error: {e}")

    def test_06_account_deletion(self):
        """Test account deletion functionality"""
        with self.subTest("Create and delete an account"):
            try:
                self.app.create_account_menu()
                self.app.new_username_entry.insert(0, "delete_test")
                self.app.new_password_entry.insert(0, "delete_pass")
                self.app.attempt_create_account()

                self.app.login_menu()
                self.app.username_entry.insert(0, "delete_test")
                self.app.password_entry.insert(0, "delete_pass")
                self.app.attempt_login()

                self.app.delete_account()

                self.app.login_menu()
                self.app.username_entry.insert(0, "delete_test")
                self.app.password_entry.insert(0, "delete_pass")
                login_result = self.app.attempt_login()

                self.assertFalse(login_result)
            except Exception as e:
                self.fail(f"Unexpected error: {e}")


if __name__ == "__main__":
    unittest.main()
