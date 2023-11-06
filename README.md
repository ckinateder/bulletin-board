# bulletin-board

## Description

### Part 1
In the first part of this project, you will consider that all clients belong to one and only one public group. A client
joins by connecting to a dedicated server (a standalone process) and is prompted to enter a non-existent user name
in that group. Note: in this project, you are not required to implement any user authentication mechanisms. The
server listens on a specific non-system port endlessly. The server keeps track of all users that join or leave the group.
When a user joins or leaves the group, all other connected clients get notified by the server. When a user (or client)
joins the group, he/she can only see the last 2 messages that were posted on the board by other clients who joined
earlier. A list of users belonging to the group is displayed once a new user joins (in this part, the list represents all
users/clients that have joined earlier). When a user posts a new message, other users in the same group should see
the posted message. Messages are displayed in the following format: “Message ID, Sender, Post Date, Subject.” A
user can retrieve the content of a message by contacting the server and providing the message ID as a parameter.
Your client program should also provide the option to leave the group. Once a user leaves the group, the server
notifies all other users in the same group of this event.

### Part 2
Extend Part 1 to allow users to join multiple private groups. Once a user is connected to the server, the server
provides a list of 5 groups. The user can then select the desired group by id or by name. A user can join multiple
groups at the same time. Remember that a user in one group cannot see users in other groups as well as the messages
they have posted to their private board in other groups.

## Protocol Design

I am using plain text to communicate between the client and the server. The client sends a command to the server
and the server responds with a message. I was going to use JSON, but I decided to keep it simple for now. This is 
inspired by Minecraft's protocol.

### Client Commands 

| Command | Description | Example | 
| --- | --- | --- |
| `/connect <host>:<port>` | connect to host:port | `/connect localhost:8080` |
| `/disconnect` | disconnect from the server | `/disconnect` |
| `/setuser <username>` | set the username | `/setuser calvin` |

**TODO**: add these commands
| Command | Description | Example | 
| --- | --- | --- |
| `/join <group>` | join a group | `/join group1` |
| `/leave <group>` | leave a group | `/leave group1` |
| `/groups` | list all groups | `/groups` |
| `/users` | list all users in the current group | `/users` |

## Usage
Make sure you are in the dev container. Otherwise, any standard implementation of Python 3.12 should work.

From the root directory of this project, start the server with `python server/main.py --host <host> --port <port>`. Then, start the client with `python client/main.py`. The client will prompt you for a command. Type `/connect <host>:<port>` to connect to the server. Then, you can type `/disconnect` to disconnect from the server. **For development, I made the server create a `.env` file to pass the host and port the server is on to the client. I'll remove it later.**

