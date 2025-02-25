# Engineering Notebook Documentation 
## gRPC and Protos Design 
We create a `protos/app.proto` file which is our Protocol Buffer definition file. It defines the data structures (message) and the methods (services) that can be used to communicate in our system. Because Protobufs are language agnostic (allows us to scale for different clients that use different languages and specifications), we need to generate python-specific proto code via the command: 

```
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. --mypy_out=. protos/app.proto
```
Our auto generated python code is housed in the protos file. 

We now enumerate the structure of our Protocol Buffer definition file. We have two message structures which define how data will be exchanged between systems. We call the two `Request` and `Response` where in the Request, we have the specific info we would like to send over (in a list) and in the Response, we offer the Operational enum and the specific info we would like to send over (such as a message). The Operational enum indicates whether the request was processed successfully or unsuccessfully with more detailed specification. 

Further we define 7 different methods under the app service which specify remote procedure calls (RPCs). Each rpc takes in a Request and outputs a Response. Each method specifies each action that our client/server application enables. 

#### Does the use of this tool make the application easier or more difficult? 

The use of gRPC makes our chat application disproportionately easier to implement. First, gRPC abstracts the difficulties of serializing and deserializing data. In our wire protocol implementation, not only did we have to design how to format the data we’d send over from the client to the server and vice versa, but we also specified the constraints for how the data would be serialized and deserialized via our wire protocol implementation. The most difficult part was figuring out how to robustly delineate different pieces of data sent over the wire and in cases where the length of the data was indeterminate (ie. with lists), we would need to recursively implement our wire protocol. gRPC abstracts the deserialization and serialization of data over the wire. Indeed, all high-level information about the structure of data sent over the wire between different commands is simply listed in the a .proto file. Developers define the structure of the data sent over via the messages keyword. For example, to send over a list of messages, our chat app now simply creates a gRPC service with an RPC called RPCReadMessage which takes in a Request and outputs a Response. Our Response, which ought to include the list of messages to read includes a repeated Message messages variable that is simply a list of Message objects defined by our protos file under the “message” keyword. By offering simple instructions for how to define data structures within the protos file, gRPC offers a standardized and robust way to send information over the wire, abstracting the serialization and deserialization component. 

Indeed, not only do we now not have to serialize and deserialize, we also do not have to worry about setting up multiple socket connections in the server (one socket for each client). gRPC abstracts those processes for us so that to start a multi-client + server application, we simply need to create a gRPC server and a gRPC stub for each client we start! This abstraction is possible because in gRPC, the stub acts as the client-side object that proxies for the remote service. Because the stub is created from the auto-generated gRPC protocol buffer file (app.protos), when you call a method on the stub, the request is automatically sent to the server which is also created and connected to the auto-generated gRPC protocol buffer file. Accordingly the network communication is entirely abstracted making the entire build-out for the application much easier to scale and implement. 

#### What does it do to the size of the data passed? 


#### How does it change the structure of the client? The server? 

Within our app.py file which specifies the chat app’s UI and starting the server and client connections, we simply change how we initialize and connect our server and client. Specifically, when “server” is chosen, we begin our run_server method which creates a new grpc server instance. We use a ThreadPoolExecutor with 10 working threads to handle concurrent requests so that we can process incoming requests in parallel. 

We then register our Server() class instance (where our rpc methods are implemented) with the grpc server instance we just instantiated. Lastly, we set up our server to listen to our port. 

On the client side, when “client” is selected, we use grpc to set up a channel with the host:port address that the server is listening on before creating a stub which provides the methods that match the server definitions to our proto file. Because the stub is created from the auto-generated gRPC protocol buffer file (app.protos), when you call a method on the stub, the request is automatically sent to the server which is also created and connected to the auto-generated gRPC protocol buffer file. 

Beyond the initialization of the client and server within the app.py file, gRPC abstracts away the serialization and the socket polling connections, making the structure of our code far easier to read. Specifically, within the server-side, each method matches the rpc service methods delineated in the protocol buffer file (app.protos). This ensures that when our client stub calls a specific method, the stub is able to 1:1 match the protos code to the server code which houses the actual implementation. From there, the server decouples the information sent over the wire. If, for example, the client sends a message, specifying in the info section of the Request that the information is a list with the sender’s username, receiver’s username, and the actual message, then to access that information, the Server simply has to check that the provided requests’s info tag has a length greater than 3 and then decouples the info tag (request.info) into the sender, receiver, and message. It then performs the necessary operations to successfully send the message before returning a Response with the specified parameters. The same flow is applied to the client-side where instead of sending over a Response, the client sends over a Request, waiting to receive the Response from the server-side. 

#### How does this change the testing of the application?


