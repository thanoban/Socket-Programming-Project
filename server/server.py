import socket
import threading

# Dictionary to store connected clients
# Key: client_name, Value: client_socket
clients = {}

# ---------------------------------------------
# Function to handle each client
# ---------------------------------------------
def handle_client(client_socket):
    try:
        # First message from client: its name
        client_name = client_socket.recv(1024).decode()
        clients[client_name] = client_socket
        print(f"[CONNECTED] {client_name} connected.")

        while True:
            # Receive the target client name
            target = client_socket.recv(1024).decode()
            if not target:
                continue

            # Receive the header: either "TEXT" or "filename|filesize"
            header = client_socket.recv(1024).decode()
            if "|" in header:  # File transfer
                filename, filesize = header.split("|")
                filesize = int(filesize)

                # Receive file data in chunks
                received_bytes = 0
                file_data = b""
                while received_bytes < filesize:
                    chunk = client_socket.recv(min(1024, filesize - received_bytes))
                    if not chunk:
                        break
                    file_data += chunk
                    received_bytes += len(chunk)

                # Forward file to target client
                if target in clients:
                    try:
                        clients[target].send(header.encode())  # send filename|filesize
                        clients[target].sendall(file_data)     # send file data
                        print(f"[FILE] {filename} forwarded from {client_name} to {target}")
                    except Exception as e:
                        print(f"[ERROR] Could not forward file: {e}")
            else:  # Text message
                if target in clients:
                    try:
                        clients[target].send(header.encode())
                        print(f"[MSG] Forwarded message from {client_name} to {target}")
                    except Exception as e:
                        print(f"[ERROR] Could not forward message: {e}")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        # Remove client on disconnect
        for name, sock in list(clients.items()):
            if sock == client_socket:
                del clients[name]
        client_socket.close()
        print(f"[DISCONNECTED] {client_name}")


# ---------------------------------------------
# Main server function
# ---------------------------------------------
def main():
    HOST = "0.0.0.0"  # Listen on all interfaces (cloud/public IP)
    PORT = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[SERVER RUNNING] Listening on {HOST}:{PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()


# ---------------------------------------------
# Run the server
# ---------------------------------------------
if __name__ == "__main__":
    main()
