# CS 2620 - Chat App

This repository contains the code for Design Exercise 1: Wire Protocol for Harvard's CS 2620: Distributed Programming class. The chat app lives entirely on the terminal, and it supports the following features.

### Features

- Creating and logging in to an account. We use a secure hashing algorithm to keep the password safe, and upon login, we allow the user to see how many unread messages they have. We do not allow for the same user to log in to multiple different devices.
![Login Screen](images/login.png)

- Listing accounts. At the home page before logging in, we allow a user to search for a particular account(s). If the search phrase is a prefix of any usernames in our database, we return a list of such usernames.
- Sending a message to a recipient. If the recipient is logged in, the app delivers immediately and notifies the recipient that they have a message. Otherwise, the message is enqueued and the recipient receives it later when they are logged in.
- Reading messages. The user will be able to view how many messages they have currently, and they can enter how many messages they wish to view (starting from messages sent more recently).
- Deleting messages. We allow a user to delete messages, which will delete the messages permanently between sender and recipient. The recipient will also have the message deleted from their account.
- Deleting an account. We allow the user to confirm deletion of their account. Deleting account keeps all messages already sent in the database. If the user is logged in on two different devices, deletion of the account prevents the user on the other device from making any changes.

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
python app.py
```

to activate the chat app and then initialize the server. Run the same command again and initialize a client. Now, you can send and receive messages.

### Architecture

#### Files

##### app.py

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

This contains helper functions related to hashing.

##### requirements.txt

This contains the list of packages we need for the app.

#### Protocol

We encode using both our own wire protocol and JSON. Both the client and server return a raw dictionary containing the operation version (JSON or our own protocol), operation type (read, send, delete message, create account, etc.), and the actual data we are sending over. We then encode (and decode) our data, and the exact specifications are determined by whether we use our wire protocol or JSON.

For the wire protocol, we encode our data through the python .encode() function. Our raw data is a dictionary that contains the following keys: version, operation, and info. The version is a one byte string, the operation is a two byte string, and the info is a list of dictionaries that has a variable size. We pack the info via the following process: for each dictionary in the list, we encode each key and value using the utf-8 format while prepending the length of the key and the length of the value in bytes to a byte string. We return all the packed dictionaries together in a single byte string. Whenever we send from the client to server or vice versa, our convention is the following: we first send a header of fixed size that contains the size of our packed data, and then we read in the data by reading in the number of bytes required to read the packed info as given by the first send system call. When we decode, we want to return the same raw dictionary that the client/server sent through, which includes the operation, version, and message. To do so, we reverse our packing operation, which is made convenient since we store the length of each key or value in the dictionary as fixed-size integers. We are thus able to read in the number of bytes needed to read in a given key or value, and then decode said key/value to return the operation, version, and message.

For the JSON, we use the json python library. To encode the data, we still use the same format of a dictionary with version, operation, and info use the json.dumps() function. Decoding, on the other hand, uses the json.loads() function, which consequently returns the version, operation, and info over the network between client and server.
