
import socket
import threading
import os
import sys

# --- Configuration (MUST CHANGE) ---
# Replace 'YOUR_AZURE_PUBLIC_IP' with the actual IP address of your Azure VM
SERVER_HOST = '13.51.170.69'
SERVER_PORT = 5000  # Must match the port opened in your Azure NSG
FORMAT = 'utf-8'

# --- Protocol Constants ---
TEXT_HEADER = "TEXT|"
FILE_HEADER_PREFIX = "FILE|"
BUFFER_SIZE = 1024

# --- Global Client Variables ---
client_socket = None
client_name = ""


def receive_handler():
    """Handles receiving and processing data from the server."""
    while True:
        try:
            # 1. Receive the protocol header from the server
            protocol_header = client_socket.recv(BUFFER_SIZE).decode(FORMAT)

            if not protocol_header:
                # Server disconnected gracefully
                print("\n[DISCONNECTED] Server closed the connection.")
                break

            if protocol_header.startswith(TEXT_HEADER):
                # --- A. Handle Text Message ---

                # Receive the full message payload
                # Note: In a real-world scenario, you'd use a fixed-length header
                # to know the exact size of the message payload.
                message_content = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
                print(f"\n[INCOMING CHAT]: {message_content}")

            elif protocol_header.startswith(FILE_HEADER_PREFIX):
                # --- B. Handle File Transfer ---

                # Extract filename and size: FILE|filename|filesize
                parts = protocol_header.split('|')
                if len(parts) != 3:
                    print("\n[ERROR] Invalid file header received.")
                    continue

                filename = parts[1]
                filesize = int(parts[2])

                print(f"\n[INCOMING FILE] Receiving '{filename}' ({filesize} bytes)...")

                # Create a file in the current directory
                with open(filename, 'wb') as f:
                    received_bytes = 0
                    while received_bytes < filesize:
                        # Receive file chunk. Use min() to not read beyond file size.
                        chunk = client_socket.recv(min(BUFFER_SIZE, filesize - received_bytes))
                        if not chunk:
                            break
                        f.write(chunk)
                        received_bytes += len(chunk)

                print(f"[FILE RECEIVED] '{filename}' saved successfully.")

            else:
                # Catch-all for server broadcasts (e.g., connection/disconnection messages)
                print(f"\n[SERVER NOTIFICATION]: {protocol_header}")

        except ConnectionResetError:
            print("\n[CONNECTION LOST] Server abruptly closed the connection.")
            break
        except Exception as e:
            print(f"\n[RECEIVE ERROR] An unexpected error occurred: {e}")
            break

    # Clean exit
    client_socket.close()
    sys.exit(0)  # Terminate the client program


def send_file(target_name, filepath):
    """Sends a file to the server for forwarding to the target."""
    if not os.path.isfile(filepath):
        print(f"Error: File not found at '{filepath}'")
        return

    try:
        filesize = os.path.getsize(filepath)
        filename = os.path.basename(filepath)

        # 1. Send Target Name
        client_socket.send(target_name.encode(FORMAT))

        # 2. Send Protocol Header: FILE|filename|filesize
        header = f"{FILE_HEADER_PREFIX}{filename}|{filesize}"
        client_socket.send(header.encode(FORMAT))

        # 3. Send File Payload
        with open(filepath, 'rb') as f:
            print(f"Sending file '{filename}' to {target_name}...")
            # Use sendall for large data to ensure all chunks are sent
            client_socket.sendall(f.read())
            print("File transfer complete.")

    except Exception as e:
        print(f"Error sending file: {e}")


def send_message(target_name, message):
    """Sends a text message to the server for forwarding to the target."""
    try:
        # 1. Send Target Name
        client_socket.send(target_name.encode(FORMAT))

        # 2. Send Protocol Header: TEXT|
        client_socket.send(TEXT_HEADER.encode(FORMAT))

        # 3. Send Message Payload
        # The server expects the sender's name in the payload
        full_message = f"[{client_name}]: {message}"
        client_socket.send(full_message.encode(FORMAT))
        print(f"Sent: {message} to {target_name}")

    except Exception as e:
        print(f"Error sending message: {e}")


def main():
    global client_socket
    global client_name

    # --- Initial Connection Setup ---
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
    except Exception as e:
        print(f"Failed to connect to server at {SERVER_HOST}:{SERVER_PORT}. Check IP/Port and server status.")
        print(f"Error: {e}")
        return

    # 1. Get Client Name and Send to Server
    client_name = input("Enter your unique client name (e.g., HostA, HostB): ")
    # The server expects the name as the very first packet
    client_socket.send(client_name.encode(FORMAT))
    print(f"\n[CONNECTED] Logged in as {client_name}. Type 'help' for commands.")

    # 2. Start the Receiving Thread
    # Daemon ensures the thread terminates when the main program exits
    receive_thread = threading.Thread(target=receive_handler, daemon=True)
    receive_thread.start()

    # 3. Main Send Loop
    while True:
        try:
            command = input(f"\n[{client_name}]> ").strip()

            if command.lower() == 'help':
                print("\n--- Commands ---")
                print("1. Text Chat: **msg <target_name> <your message>**")
                print("2. File Transfer: **file <target_name> <path/to/file>**")
                print("3. Quit: **quit**")
                print("----------------\n")

            elif command.lower().startswith('msg'):
                parts = command.split(' ', 2)
                if len(parts) == 3:
                    send_message(parts[1], parts[2])
                else:
                    print("Usage: msg <target_name> <your message>")

            elif command.lower().startswith('file'):
                parts = command.split(' ', 2)
                if len(parts) == 3:
                    send_file(parts[1], parts[2])
                else:
                    print("Usage: file <target_name> <path/to/file>")

            elif command.lower() == 'quit':
                print("Disconnecting...")
                client_socket.close()
                break

            elif command:
                print("Invalid command. Type 'help' for options.")

        except EOFError:
            break
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()