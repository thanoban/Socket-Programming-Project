import socket
import threading
import os
import tkinter as tk
from tkinter import filedialog, simpledialog, scrolledtext, messagebox

# ============================================================
#  CLIENT GUI CLASS
# ============================================================
class ClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("Socket Client - Chat & File Transfer")

        # Chat Display UI
        self.chat_area = scrolledtext.ScrolledText(master, width=60, height=20)
        self.chat_area.pack(padx=10, pady=10)
        self.chat_area.config(state="disabled")

        # Message entry box
        self.msg_entry = tk.Entry(master, width=40)
        self.msg_entry.pack(side=tk.LEFT, padx=(10, 0), pady=(0, 10))
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        # Send message button
        tk.Button(master, text="Send Message", command=self.send_message).pack(
            side=tk.LEFT, padx=(5, 0), pady=(0, 10)
        )

        # Send file button
        tk.Button(master, text="Send File", command=self.send_file).pack(
            side=tk.LEFT, padx=(5, 10), pady=(0, 10)
        )

        # ===============================
        # Ask user important details
        # ===============================

        self.server_ip = simpledialog.askstring("Server IP", "Enter server IP:")
        self.server_port = 5000

        self.client_name = simpledialog.askstring(
            "Client Name", "Enter your client name (Example: PC1, PC2, CLOUD):"
        )

        self.target_client = simpledialog.askstring(
            "Target Client", "Enter target client name to communicate with:"
        )

        # ===============================
        # Connect to server
        # ===============================
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect: {e}")
            master.destroy()
            return

        # Send client name to server
        self.client_socket.send(self.client_name.encode())

        # Local client IP
        local_ip = socket.gethostbyname(socket.gethostname())

        # Display connection info
        self.chat_area.config(state="normal")
        self.chat_area.insert(
            tk.END, f"[CONNECTED] Connected to server {self.server_ip}:{self.server_port}\n"
        )
        self.chat_area.insert(tk.END, f"[LOCAL CLIENT IP] {local_ip}\n")
        self.chat_area.insert(tk.END, f"[CLIENT NAME] {self.client_name}\n")
        self.chat_area.insert(tk.END, f"[TARGET CLIENT] {self.target_client}\n\n")
        self.chat_area.config(state="disabled")

        # Start receiving thread
        threading.Thread(target=self.receive_from_server, daemon=True).start()

    # ============================================================
    # SEND TEXT MESSAGE
    # ============================================================
    def send_message(self):
        msg = self.msg_entry.get()
        if msg.strip() == "":
            return

        try:
            self.client_socket.send(self.target_client.encode())
            self.client_socket.send(msg.encode())

            self.chat_area.config(state="normal")
            self.chat_area.insert(
                tk.END, f"[YOU → {self.target_client}] {msg}\n"
            )
            self.chat_area.config(state="disabled")
            self.msg_entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Send Error", f"Cannot send message: {e}")

    # ============================================================
    # SEND FILE
    # ============================================================
    def send_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        try:
            self.client_socket.send(self.target_client.encode())
            self.client_socket.send(f"{filename}|{filesize}".encode())

            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    self.client_socket.sendall(chunk)

            self.chat_area.config(state="normal")
            self.chat_area.insert(
                tk.END, f"[YOU → {self.target_client}] File sent: {filename}\n"
            )
            self.chat_area.config(state="disabled")

        except Exception as e:
            messagebox.showerror("File Error", f"Cannot send file: {e}")

    # ============================================================
    # RECEIVE MESSAGES / FILES
    # ============================================================
    def receive_from_server(self):
        while True:
            try:
                header = self.client_socket.recv(1024).decode()
                if not header:
                    continue

                if "|" in header:  # File transfer
                    filename, filesize = header.split("|")
                    filesize = int(filesize)
                    received = 0

                    with open(f"received_{filename}", "wb") as f:
                        while received < filesize:
                            chunk = self.client_socket.recv(min(1024, filesize - received))
                            if not chunk:
                                break
                            f.write(chunk)
                            received += len(chunk)

                    self.chat_area.config(state="normal")
                    self.chat_area.insert(
                        tk.END, f"[RECEIVED FILE] {filename} saved as received_{filename}\n"
                    )
                    self.chat_area.config(state="disabled")

                else:  # Text message
                    self.chat_area.config(state="normal")
                    self.chat_area.insert(tk.END, f"[MESSAGE] {header}\n")
                    self.chat_area.config(state="disabled")

            except:
                break


# ============================================================
# MAIN APP RUNNER
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    gui = ClientGUI(root)
    root.mainloop()
