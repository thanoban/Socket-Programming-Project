

import socket
import threading

clients = set()
lock = threading.Lock()

def broadcast(sender, msg):
    with lock:
        for conn in clients:
            try:
                conn.sendall(f"{sender}|{msg}\n".encode())
            except:
                pass

def handle_client(conn, addr):
    name = None
    try:
        # Read username
        buffer = ""
        while "\n" not in buffer:
            chunk = conn.recv(1024)
            if not chunk:
                return
            buffer += chunk.decode("utf-8", errors="ignore")

        name = buffer.split("\n", 1)[0].strip()
        leftover = buffer.split("\n", 1)[1] if "\n" in buffer else ""

        if name == "":
            conn.close()
            return

        with lock:
            clients.add(conn)

        print(f"[+] {name} joined")

        broadcast("System", f"{name} joined the chat")

        
        buffer = leftover

        while True:
           
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    broadcast(name, line)

        
            chunk = conn.recv(1024)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="ignore")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        with lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()
        print(f"[-] {name} left")
        if name:
            broadcast("System", f"{name} left the chat")
            

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", 5000))
s.listen(50)
print("Broadcast Chat Server Running on port 5000...")

while True:
    conn, addr = s.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
