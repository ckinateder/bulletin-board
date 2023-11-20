# bulletin-board

## Description

### Part 1

In the first part of this project, you will consider that all clients belong to one and only one public group. A client joins by connecting
to a dedicated server (a standalone process) and is prompted to enter a non-existent user name in that group. Note: in this project, you are
not required to implement any user authentication mechanisms. The server listens on a specific non-system port endlessly. The server keeps
track of all users that join or leave the group. When a user joins or leaves the group, all other connected clients get notified by the
server. When a user (or client) joins the group, he/she can only see the last 2 messages that were posted on the board by other clients who
joined earlier. A list of users belonging to the group is displayed once a new user joins (in this part, the list represents all
users/clients that have joined earlier). When a user posts a new message, other users in the same group should see the posted message.
Messages are displayed in the following format: “Message ID, Sender, Post Date, Subject.” A user can retrieve the content of a message by
contacting the server and providing the message ID as a parameter. Your client program should also provide the option to leave the group.
Once a user leaves the group, the server notifies all other users in the same group of this event.

### Part 2

Extend Part 1 to allow users to join multiple private groups. Once a user is connected to the server, the server provides a list of 5
groups. The user can then select the desired group by id or by name. A user can join multiple groups at the same time. Remember that a user
in one group cannot see users in other groups as well as the messages they have posted to their private board in other groups.

## Protocol Design

I am using plain text to communicate between the client and the server. The client sends a command to the server and the server responds
with a message. I was going to use JSON, but I decided to keep it simple for now. This is inspired by Minecraft's protocol.

### Client Commands

| Command                  | Description                         | Example                   |
| ------------------------ | ----------------------------------- | ------------------------- |
| `/connect <host>:<port>` | connect to host:port                | `/connect localhost:8080` |
| `/disconnect`            | disconnect from the server          | `/disconnect`             |
| `/setuser <username>`    | set the username                    | `/setuser calvin`         |
| `/join <group>`          | join a group                        | `/join group1`            |
| `/leave <group>`         | leave a group                       | `/leave group1`           |
| `/users`                 | list all users in the current group | `/users`                  |

**TODO**: add these commands and more | Command | Description | Example | | --- | --- | --- | | `/groups` | list all groups | `/groups` |

## Server Design

The server is a standalone process that listens on a port. It accepts connections from clients and spawns a new thread for each client. The
server keeps track of all connected clients and the groups they are in. The server also keeps track of all messages posted to the board. The
server is responsible for sending messages to clients. The server is also responsible for sending messages to other clients when a client
joins or leaves a group.

There exists a `Lobby`, which holds multiple `Board`s. A `Board` holds multiple `Message`s and multiple `User`s. A `User` can be in multiple
`Board`s. A `User` can post a `Message` to a `Board`. A `User` can also join or leave a `Board`. A `Message` has one `User` as its author. A
`Message` also has a `Board` as its parent. A `Board` has a `Lobby` as its parent.

## Usage

Make sure you are in the dev container if you are in VSCode. Otherwise, any standard implementation of Python 3.11 or higher will work.

From the root directory of this project, start the server with `python server/main.py --host <host> --port <port>`. Then, start the client
with `python client/main.py`. The client will prompt you to enter your username and then for commands. Type `/connect <host>:<port>` to
connect to the server. Then, you can type `/disconnect` to disconnect from the server. **For development, I made the server create a `.env`
file to pass the host and port the server is on to the client. I'll remove it later.**

## Messages

Client

```json
{
    "id": "0x1234567",
    "command": 1,
    "acknowledgementId": null,
    "body": {
        "host": "123.0.0.1",
        "port": 12345
    }
}
```

Server

```json
{
    "id": "id",
    "command": 5,
    "run_without_id_check": true,
    "is_success": true,
    "acknowledgement_id": "acknowledgement_id",
    "body": {
        "username": "joe",
        "post": "hi",
        "board": "main"
    }
}
```
