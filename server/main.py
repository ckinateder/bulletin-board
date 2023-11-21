# echo-server.py
import socket
import argparse
from Server import Server
from Lobby import Lobby
from ClientConnection import ClientConnection

DEFAULT_HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
DEFAULT_PORT = 64538  # Port to listen on (non-privileged ports are > 1023)


def main(host: str, port: int, server: Server):
    """Runs the server.

    Args:
        host (str): host
        port (int): port
        lobby (Lobby): lobby
    """
    s = socket.socket()
    s.bind((host, port))  # bind the socket to the port and ip address
    s.listen(5)  # wait for new connections

    try:
        while True:
            c, addr = s.accept()  # Establish connection with client.
            # this returns a new socket object and the IP address of the client
            print(f"New connection from: {addr}")
            c.sendall("".encode())
            server.new_connection(c, addr)
    except KeyboardInterrupt:
        print("Closing server...")
        s.close()
    print(server.lobby.log)


if __name__ == "__main__":
    # set the args
    parser = argparse.ArgumentParser(
        prog="Bulletin Board Server",
        description="Runs a server for a bulletin board.",
        epilog="See the README for more information.",
    )
    parser.add_argument("-H", "--host", type=str, default=DEFAULT_HOST)
    parser.add_argument("-P", "--port", type=int, default=DEFAULT_PORT)

    # parse the arguments
    args = parser.parse_args()

    # add into environment variables
    with open(".env", "w+", encoding="utf-8") as f:
        f.write(f"{args.host}:{args.port}\n")

    # create the lobby and add a default board
    boards = Lobby()
    boards.new_board("default")
    server = Server(boards)
    # run the server
    print(
        f"Welcome to the Bulletin Board Server! Listening on {args.host}:{args.port}..."
    )
    main(args.host, args.port, server)
