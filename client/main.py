import socket

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65431 # The port used by the server

print("Welcome! Type 'help' for a list of commands.")
"""
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"Connecting to {HOST}:{PORT}...")
    s.connect((HOST, PORT))
    print("Connected!")

    while to_send := input("> ") != "exit":
        s.sendall(to_send.encode())
        data = s.recv(1024)
        print(f"Received {data!r}")
"""
server = None # not connected yet
host, port = None, None
client_id = None #prefix this to every message. get told this bv server

#server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#server.connect((HOST, PORT))
#print(f"connected to {HOST}:{PORT}")
        
while prompt_response := input("> ").strip():
    if prompt_response == "%help":
        print("Commands:")
        print("%connect <host>:<port> - connect to a server")
        print("%send <message> - send a message to the server")
        print("%exit - exit the program")

    if prompt_response[:8] == "%connect":
        if server:
            print(f"You are already connected to {host}:{port}, please disconnect first.")
            continue
        # get the username
        username = input("Enter your username: ")

        # parse the response to get the host and port
        host, port = prompt_response[9:].split(":")
        host = host.strip()
        port = int(port)
        # connect to the server
        try:
            print(f"Connecting to {host}:{port}...", end=" ")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            print(f"success!")
            #data = sock.recv(1024)
            #print(f"Received id {data!r}")
            
            # get username here
            sock.sendall(f"/user {username}".encode())
            #data = sock.recv(1024)
            #print(f"Received {data!r}")
        except socket.gaierror:
            print(f"failure. Name or service not known '{host}'")
        except ConnectionRefusedError:
            print(f"failure. Connection refused by '{host}:{port}'")
        except Exception as e:
            print("failure. Unknown error.")

    elif prompt_response == "%disconnect":
        # check if we're connected
        if not server:
            print("You are not connected to a server yet.")
            continue

        # disconnect from the server
        server.close()
        server = None
        print("Disconnected!")
    elif prompt_response[:5] == "%send":
        # check if we're connected
        if not server:
            print("You are not connected to a server yet.")
            continue

        # send the message to the server
        server.sendall(prompt_response[6:].encode())
        data = server.recv(1024)
        print(f"Received {data!r}")

        print("Sent!")
    elif prompt_response == "%exit":
        # exit the program
        print("Exiting...")
        server.close()
        break
    else:
        print("Invalid command. Type '%help' for a list of commands.")