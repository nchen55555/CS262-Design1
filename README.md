# CS 2620 - Chat App
This repository contains the code for Design Exercise 1: Wire Protocol for Harvard's CS 2620: Distributed Programming class. The chat app lives entirely on the terminal, and it supports the following features.
### Features
- Creating and logging in to an account. We use a secure hashing algorithm to keep the password safe, and upon login, we allow the user to see how many unread messages they have.
- Listing accounts. We allow a user to search for a particular account(s).
- Sending a message to a recipient. If the recipient is logged in, the app delivers immediately and notifies the recipient that they have a message. Otherwise, the message is enqueued and the recipient receives it later when they are logged in.
- Reading messages. The user will be notified of unread messages and be allowed to specify how many messages they want at a time.
- Deleting messages. We allow a user to delete messages, which will delete the messages permanently between sender and recipient.
- Deleting an account. We allow the user to confirm deletion of their account.
### Setup
To setup, we first require people to clone our repository via
```
git clone https://github.com/nchen55555/CS262-Design1.git
```
After, we require the user to have Python3 and pip installed on their system. To install the necessary packages, run
```
pip3 install -r requirements.txt
```
Now, we can finally use the chat app. The server handles all client/user interactions, so we need to set the server up first. Run
```
python chat_screen.py
```
to activate the chat app, and press "2" on the menu to initialize the server. Now, run the same command again and press "1" on the menu to initialize a client and thereby send and receive messages.
### Architecture
#### Files
##### chat_screen.py
This file starts up the app for either the client or the server.
##### protocol_client.py
This contains the code for the client/user side of the app.
##### protocol_server.py
This contains the server code, which handles multiple client connections.
##### wire_protocol.py
This contains the packing and unpacking function for the wire protocol, which allows data to be encoded and then decoded when sent over from and to the server.
##### operations.py
This maps the operations we support (read/send message, etc.) to specific numbers that we can later reference in our wire protocol.
##### message.py
This contains the class for the messages, which is structured so that every message has a sender, recipient, message itself, and the time it was sent
##### user.py
This contains the class for the users, structured around the username and hashed password, and also including the user's messages and unread messages.
##### test.py
This contains unit tests that we use to test the effectiveness of our app.
##### util.py
This contains helper functions related to hashing and the GUI for our app.
##### requirements.txt
This contains the list of packages we need for the app.
#### Protocol
We encode using both our own wire protocol and JSON. Both the client and server return a raw dictionary containing the operation version (JSON or our own protocol), operation type (read, send, delete message, create account, etc.), and the actual data we are sending over. 
We encode our data through the python .encode() function, and when we decode, we expect to see the same info: operation, version, and message.
The server and client both send messages through the following convention: we first send the message length, and then we send the actual message so that the server/client knows exactly how many bytes of data to read.
