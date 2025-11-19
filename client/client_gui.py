import socket
import threading
import os
import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

# --- Configuration ---
SERVER_HOST = "20.193.158.234"   # Change if needed
SERVER_PORT = 5000
FORMAT = "utf-8"
BUFFER_SIZE = 4096  # Increased for faster file transfer

client_socket = None
client_name = ""
connected = False


# ============================================================
#  RECEIVE HANDLER (Runs in background)
# ============================================================
def receive_handler(gui):
    global client_socket, connected

    while connected:
        try:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                gui.write_chat("\n[DISCONNECTED] Server closed the connection.")
                break

            message = data.decode(FORMAT, errors='ignore')

            # Handle incoming TEXT messages
            if message.startswith("TEXT|"):
                # Format: TEXT|From: Alice|Hello!
                parts = message.split("|", 2)
                if len(parts) == 3:
                    sender = parts[1]
                    text = parts[2]
                    gui.write_chat(f"\n{sender} → You: {text}")
                else:
                    gui.write_chat(f"\n[Message] {message[5:]}")

            # Handle file transfer
            elif message.startswith("FILE|"):
                # Expected next: filename and size already in header
                header = message
                parts = header.split("|")
                if len(parts) < 3:
                    continue
                filename = parts[1]
                try:
                    filesize = int(parts[2])
                except:
                    continue

                gui.write_chat(f"\n[Incoming File] {filename} ({filesize} bytes)")

                save_path = os.path.join(os.getcwd(), "Received_" + filename)
                with open(save_path, "wb") as f:
                    received = 0
                    while received < filesize:
                        chunk = client_socket.recv(min(BUFFER_SIZE, filesize - received))
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)

                gui.write_chat(f"\n[File Saved] → {os.path.basename(save_path)}")

            else:
                # Any other message (server broadcast, etc.)
                gui.write_chat(f"\n[SERVER] {message}")

        except (ConnectionResetError, BrokenPipeError, OSError):
            gui.write_chat("\n[ERROR] Lost connection to server.")
            break
        except Exception as e:
            gui.write_chat(f"\n[RECV ERROR] {str(e)}")
            break

    # --- Safely mark as disconnected ---
    connected = False
    try:
        client_socket.close()
    except:
        pass

    gui.write_chat("\nYou are now disconnected. Close window to exit.")


# ============================================================
#  SEND MESSAGE
# ============================================================
def send_message(target, msg):
    global client_socket, connected
    if not connected or not client_socket:
        return False

    try:
        full_msg = f"TEXT|{target}|[{client_name}]: {msg}"
        client_socket.sendall(full_msg.encode(FORMAT))
        return True
    except:
        return False


# ============================================================
#  SEND FILE
# ============================================================
def send_file(target, filepath, gui):
    global client_socket, connected
    if not connected or not client_socket:
        gui.write_chat("\n[ERROR] Not connected to server.")
        return

    if not os.path.isfile(filepath):
        gui.write_chat("\n[ERROR] File not found.")
        return

    try:
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        header = f"FILE|{target}|{filename}|{filesize}"
        client_socket.sendall(header.encode(FORMAT))

        gui.write_chat(f"\nSending {filename} to {target}...")

        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                client_socket.sendall(chunk)

        gui.write_chat(f"\nFile sent successfully to {target}!")

    except Exception as e:
        gui.write_chat(f"\n[ERROR Sending File] {e}")


# ============================================================
#  GUI CLASS
# ============================================================
class ClientGUI:
    def __init__(self, master):
        self.master = master
        master.title(f"Chat Client - {client_name}")
        master.geometry("700x600")
        master.configure(bg="#2c3e50")

        # Chat display
        self.chat_area = scrolledtext.ScrolledText(
            master, wrap=tk.WORD, width=80, height=30,
            bg="#ecf0f1", fg="#2c3e50", font=("Helvetica", 10)
        )
        self.chat_area.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        self.chat_area.config(state=tk.DISABLED)

        # Input frame
        input_frame = tk.Frame(master, bg="#2c3e50")
        input_frame.pack(pady=10, fill=tk.X, padx=15)

        tk.Label(input_frame, text="To:", bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)
        self.target_entry = tk.Entry(input_frame, width=15, font=("Helvetica", 11))
        self.target_entry.insert(0, "pc2")  # default target
        self.target_entry.pack(side=tk.LEFT, padx=5)

        self.msg_entry = tk.Entry(input_frame, width=50, font=("Helvetica", 11))
        self.msg_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", lambda e: self.send_message_command())

        send_btn = tk.Button(input_frame, text="Send", bg="#27ae60", fg="white",
                             command=self.send_message_command)
        send_btn.pack(side=tk.LEFT, padx=5)

        file_btn = tk.Button(input_frame, text="Send File", bg="#2980b9", fg="white",
                             command=self.send_file_command)
        file_btn.pack(side=tk.LEFT, padx=5)

        # Initial message
        self.write_chat(f"Connected as: {client_name}\nType message and press Send or Enter.")

    def write_chat(self, msg):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, msg)
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def send_message_command(self):
        target = self.target_entry.get().strip()
        msg = self.msg_entry.get().strip()
        if not target or not msg:
            return
        if send_message(target, msg):
            self.write_chat(f"\nYou → {target}: {msg}")
        else:
            self.write_chat(f"\n[FAILED] Could not send to {target}")
        self.msg_entry.delete(0, tk.END)

    def send_file_command(self):
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("Warning", "Enter target name first!")
            return
        filepath = filedialog.askopenfilename(title="Choose file to send")
        if filepath:
            threading.Thread(target=send_file, args=(target, filepath, self), daemon=True).start()


# ============================================================
#  CONNECT SCREEN
# ============================================================
def connect_screen():
    global client_socket, connected

    def connect_action():
        global client_name, connected

        name = name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter your name!")
            return

        client_name = name

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            client_socket.send(client_name.encode(FORMAT))
            connected = True

            top.destroy()
            root.deiconify()  # Show main window

            gui = ClientGUI(root)
            threading.Thread(target=receive_handler, args=(gui,), daemon=True).start()

        except Exception as e:
            messagebox.showerror("Connection Failed", f"Cannot connect to server:\n{e}")

    top = tk.Toplevel()
    top.title("Join Chat")
    top.geometry("350x200")
    top.configure(bg="#34495e")

    tk.Label(top, text="Enter Your Name (e.g., pc1 or pc2)", bg="#34495e", fg="white", font=("Helvetica", 12)).pack(pady=20)
    name_entry = tk.Entry(top, width=25, font=("Helvetica", 11))
    name_entry.pack(pady=10)
    name_entry.focus()

    tk.Button(top, text="Connect to Server", bg="#27ae60", fg="white", font=("Helvetica", 11),
              command=connect_action).pack(pady=15)

    top.bind('<Return>', lambda e: connect_action())


# ============================================================
#  MAIN
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window until connected
    connect_screen()
    root.mainloop()