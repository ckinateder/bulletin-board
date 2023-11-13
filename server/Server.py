import socket
from User import User
from Lobby import Lobby

class Server:

    def send_to_client(self, client_socket: socket.socket, data: str):
        """Sends data to a client."""
        client_socket.sendall(data.encode())
        print(f"Sent '{data}' to {client_socket.getpeername()}")


    def on_new_client(
        self, client_socket: socket.socket, addr: tuple, lobby: Lobby
    ):  # one thread per user
        """Handles a client. One thread for each client.

        Args:
            client_socket (socket.socket): client socket
            addr (tuple): address of client
            lobby (Lobby): global lobby
        """
        user = None
        board = None  # the board the user is currently viewing
        while True:
            # receive data from client
            data = client_socket.recv(1024).decode("utf-8").strip()
            if not data:
                break

            # show what was said
            if user:
                print(f"{user.username} >> {data}")
            else:
                print(f"{addr} >> {data}")

            # handle commands
            if data[:8] == "/connect":  # /newuser <username>
                username = data[9:].strip()
                if (
                    username in lobby.users.get_all_usernames() or username == ""
                ):  # unsuccessful
                    self.self.send_to_client(
                        client_socket,
                        f"/fail name_taken {':'.join(lobby.users.get_all_usernames())}",
                    )
                else:  # successful
                    user = User(username, client_socket)  # create the user
                    user.connected = True  # connect the user
                    lobby.add_user_to_lobby(user)  # add the user to the list of users
                    self.send_to_client(
                        client_socket, f"/success {username}:{user.id}"
                    )  # send the success message
            elif data[:10] == "/reconnect":  # /reconnect <username>:<id>
                info = data[11:].strip()
                username, userid = info.split(":")  # get the username and id
                user = lobby.users.get_user_by_id(userid)  # get the user

                if user and user.username != username:
                    # user exists but username is wrong, name may have been changed
                    if username in lobby.users.get_all_usernames():
                        # unsuccessful, user already exists, pick a new one
                        self.send_to_client(
                            client_socket,
                            f"/fail name_taken {':'.join(lobby.users.get_all_usernames())}",
                        )
                    else:  # successful, user exists but username is wrong, name may have been changed
                        user.username = username
                        lobby.log.add(user.id, "reconnect")  # log the reconnection
                        lobby.log.add(user.id, "username_change", username)
                        self.send_to_client(client_socket, f"/success {username}:{user.id}")
                elif user and user.username == username:
                    # successful, user exists and username is correct
                    self.send_to_client(
                        client_socket, f"/success {username}:{user.id}"
                    )  # send the success message
                    user.connected = True  # connect the user
                    lobby.log.add(user.id, "reconnect")  # log the reconnection
                else:  # unsuccessful, user not found, must connect with no id
                    self.send_to_client(client_socket, "/fail no_id")
            elif data[:8] == "/chguser":  # /chguser <username>:<id>
                info = data[9:].strip()
                username, userid = info.split(":")
                if user.id != userid:  # unsuccessful
                    self.send_to_client(client_socket, f"/fail {user.username}")
                elif username in lobby.users.get_all_usernames() or username == "":
                    self.send_to_client(
                        client_socket,
                        f"/fail name_taken {':'.join(lobby.users.get_all_usernames())}",
                    )
                else:
                    user.username = username
                    lobby.log.add(user.id, "username_change", username)
                    self.send_to_client(client_socket, f"/success {username}:{user.id}")
            elif data[:5] == "/join":
                # join a board
                board_name = data[6:].strip()  # get the board name

                if board:  # if the user is already on a board
                    if board.name == board_name:
                        self.send_to_client(client_socket, f"/success {board_name}")
                        continue  # already on that board
                    else:  # user is on a different board so leave and join new one
                        lobby.remove_user_from_board(user, board.name)

                board = lobby.get_board_by_name(board_name)  # get the board
                if board:  # board exists
                    lobby.add_user_to_board(user, board_name)
                    self.send_to_client(client_socket, f"/success {board_name}")
                else:  # board does not exist
                    self.send_to_client(client_socket, f"/fail {board_name}")
            elif data[:6] == "/leave":
                # leave a board
                if board:
                    lobby.remove_user_from_board(user, board.name)
                    self.send_to_client(client_socket, f"/success {board.name}")
                else:
                    self.send_to_client(client_socket, "/fail no_board")
            elif data[:6] == "/users":
                # get all users
                if board:
                    self.send_to_client(
                        client_socket,
                        f"/success {':'.join(board.users.get_all_usernames())}",
                    )
                else:
                    self.send_to_client(client_socket, "/fail no_board")

            if not user:
                print("user not logged in.")

        # close the connection
        client_socket.close()

        # if the user was logged in, remove them from the users list and log the disconnection
        if user:
            if board:
                lobby.remove_user_from_board(user, board.name)
            user.connected = False
            lobby.log.add(user.id, "disconnect")
        print(f"Connection from {addr} closed.")
        print(f"users: {lobby.users}")
        print(lobby.log)