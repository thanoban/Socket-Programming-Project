import socket
import threading
import os
import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

# --- Configuration ---
SERVER_HOST = "13.51.170.69"  # Fixed server IP
SERVER_PORT = 5000
FORMAT = "utf-8"
BUFFER_SIZE = 1024

client_socket = None
client_name = ""


# ============================================================
#  RECEIVE HANDLER
# ============================================================
def receive_handler(gui):
    global client_socket

    while True:
        try:
            protocol_header = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
            if not protocol_header:
                gui.write_chat("\n[DISCONNECTED] Server closed connection.")
                break

            if protocol_header.startswith("TEXT|"):
                message = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
                gui.write_chat(f"\n{message}")

            elif protocol_header.startswith("FILE|"):
                parts = protocol_header.split('|')
                filename = parts[1]
                filesize = int(parts[2])

                gui.write_chat(f"\n[Incoming File] {filename} ({filesize} bytes)")

                with open(filename, "wb") as f:
                    received = 0
                    while received < filesize:
                        chunk = client_socket.recv(min(BUFFER_SIZE, filesize - received))
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)

                gui.write_chat(f"\n[File Saved] {filename}")

            else:
                gui.write_chat(f"\n[SERVER] {protocol_header}")

        except Exception as e:
            gui.write_chat(f"\n[ERROR] {e}")
            break

    client_socket.close()
    sys.exit(0)


# ============================================================
#  SEND MESSAGE
# ============================================================
def send_message(target, msg):
    try:
        client_socket.send(target.encode(FORMAT))
        client_socket.send("TEXT|".encode(FORMAT))
        full = f"[{client_name}]: {msg}"
        client_socket.send(full.encode(FORMAT))
    except Exception as e:
        print(f"Error sending message: {e}")


# ============================================================
#  SEND FILE
# ============================================================
def send_file(target, filepath, gui):
    if not os.path.isfile(filepath):
        gui.write_chat("\n[ERROR] File not found.")
        return

    try:
        filesize = os.path.getsize(filepath)
        filename = os.path.basename(filepath)

        client_socket.send(target.encode(FORMAT))

        header = f"FILE|{filename}|{filesize}"
        client_socket.send(header.encode(FORMAT))

        with open(filepath, "rb") as f:
            gui.write_chat(f"\nSending {filename}...")
            client_socket.sendall(f.read())
            gui.write_chat("\nFile sent.")

    except Exception as e:
        gui.write_chat(f"\n[ERROR] {e}")


# ============================================================
#  GUI CLASS
# ============================================================
class ClientGUI:
    def __init__(self, master):
        self.master = master
        master.title(f"Socket Client - {client_name}")
        master.geometry("650x550")
        master.configure(bg="#f0f2f5")

        # Chat Area
        self.chat_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=75, height=25, bg="#ffffff")
        self.chat_area.pack(padx=10, pady=10)
        self.chat_area.config(state=tk.DISABLED)

        # Target and Message Frame
        self.frame = tk.Frame(master, bg="#f0f2f5")
        self.frame.pack(pady=5)

        tk.Label(self.frame, text="Target Name:", bg="#f0f2f5").grid(row=0, column=0, padx=5, pady=2)
        self.target_entry = tk.Entry(self.frame, width=20)
        self.target_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(self.frame, text="Message:", bg="#f0f2f5").grid(row=1, column=0, padx=5, pady=2)
        self.msg_entry = tk.Entry(self.frame, width=50)
        self.msg_entry.grid(row=1, column=1, padx=5, pady=2)

        # Buttons
        self.send_btn = tk.Button(master, text="Send Message", bg="#4CAF50", fg="white", command=self.send_message_command)
        self.send_btn.pack(pady=5, ipadx=10, ipady=5)

        self.file_btn = tk.Button(master, text="Send File", bg="#2196F3", fg="white", command=self.send_file_command)
        self.file_btn.pack(pady=5, ipadx=10, ipady=5)

    def write_chat(self, msg):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, msg)
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def send_message_command(self):
        target = self.target_entry.get().strip()
        msg = self.msg_entry.get().strip()

        if not target or not msg:
            messagebox.showerror("Error", "Target and message required.")
            return

        send_message(target, msg)
        self.write_chat(f"\n[You -> {target}]: {msg}")
        self.msg_entry.delete(0, tk.END)

    def send_file_command(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showerror("Error", "Target name required.")
            return

        filepath = filedialog.askopenfilename()
        if filepath:
            send_file(target, filepath, self)


# ============================================================
#  CONNECT SCREEN (ASK ONLY CLIENT NAME)
# ============================================================
def connect_screen():
    def connect_action():
        global client_socket, client_name

        client_name_input = name_entry.get().strip()
        if not client_name_input:
            messagebox.showerror("Error", "Enter client name.")
            return

        client_name = client_name_input

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            client_socket.send(client_name.encode(FORMAT))
        except Exception as e:
            messagebox.showerror("Connection Failed", str(e))
            return

        top.destroy()

        gui = ClientGUI(root)
        threading.Thread(target=receive_handler, args=(gui,), daemon=True).start()

    top = tk.Toplevel()
    top.title("Connect to Server")
    top.geometry("300x150")
    top.configure(bg="#f0f2f5")

    tk.Label(top, text="Enter Client Name:", bg="#f0f2f5").pack(pady=10)
    name_entry = tk.Entry(top, width=30)
    name_entry.pack(pady=5)

    tk.Button(top, text="Connect", bg="#4CAF50", fg="white", command=connect_action).pack(pady=20, ipadx=10, ipady=5)


# ============================================================
#  MAIN
# ============================================================
root = tk.Tk()
root.withdraw()
connect_screen()
root.mainloop()
