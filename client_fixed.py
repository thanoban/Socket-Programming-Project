

import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox


SERVER_HOST = "20.193.158.234" 
SERVER_PORT = 5000


client_socket = None
client_name = ""
connected = False

def receive_messages(text_widget):
    """Handles receiving and displaying messages from the server."""
    global connected
    buffer = ""

    while connected:
        try:
            data = client_socket.recv(2048)
            if not data:
                
                break

            buffer += data.decode("utf-8", errors="ignore")
         
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if "|" in line:
                  
                    if sender == "System":
                        text_widget.configure(state='normal')
                        text_widget.insert(tk.END, f"[{sender}] {msg}\n", "system_message")
                        text_widget.configure(state='disabled')
                    else:
                        text_widget.configure(state='normal')
                        text_widget.insert(tk.END, f"<{sender}> {msg}\n")
                        text_widget.configure(state='disabled')
                    text_widget.see(tk.END) 
                
        except socket.error as e:
            
            print(f"Socket error during receive: {e}")
            break
        except Exception as e:
            print(f"An unexpected error occurred during receive: {e}")
            break

  
    if connected:
        connected = False
        text_widget.configure(state='normal')
        text_widget.insert(tk.END, "\n[System] Disconnected from the server.\n", "system_message")
        text_widget.configure(state='disabled')
        text_widget.see(tk.END)
        messagebox.showinfo("Disconnected", "You have been disconnected from the chat server.")
    
    if client_socket:
        client_socket.close()

def send_message(entry_widget, text_widget):
    """Handles sending messages from the client to the server."""
    global client_name, client_socket, connected

    if not connected:
        messagebox.showerror("Not Connected", "You are not connected to the server.")
        return

    message = entry_widget.get().strip()
    if not message:
        return

    try:
   
        client_socket.sendall((message + "\n").encode("utf-8"))
  
        text_widget.configure(state='normal')
        text_widget.insert(tk.END, f"<You> {message}\n", "my_message")
        text_widget.configure(state='disabled')
        text_widget.see(tk.END) 
        entry_widget.delete(0, tk.END) 

    except socket.error as e:
        messagebox.showerror("Send Error", f"Failed to send message: {e}")
    
        text_widget.configure(state='normal')
        text_widget.insert(tk.END, f"\n[System] Failed to send message. Connection might be lost.\n", "system_message")
        text_widget.configure(state='disabled')
        connected = False 
        if client_socket:
            client_socket.close()
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred while sending: {e}")


def connect_to_server(root, text_widget):
    """Establishes connection to the server and starts receive thread."""
    global client_name, client_socket, connected


    name = simpledialog.askstring("Username", "Enter your desired username:", parent=root)
    if not name or name.strip() == "":
        messagebox.showwarning("Username Required", "A username is required to join the chat.")
        root.quit() 
        return

    client_name = name.strip()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        
        
        client_socket.sendall(f"{client_name}\n".encode("utf-8"))

        connected = True
       
        threading.Thread(target=receive_messages, args=(text_widget,), daemon=True).start()

        text_widget.configure(state='normal')
        text_widget.insert(tk.END, f"[System] Connected to chat as {client_name}!\n", "system_message")
        text_widget.configure(state='disabled')
        text_widget.see(tk.END)

    except ConnectionRefusedError:
        messagebox.showerror("Connection Failed", 
                             f"Could not connect to the server at {SERVER_HOST}:{SERVER_PORT}.\n"
                             "Please ensure the server is running and the IP address is correct.")
        root.quit()
    except socket.gaierror:
        messagebox.showerror("Connection Failed", 
                             f"Invalid server address: {SERVER_HOST}.\n"
                             "Please check the SERVER_HOST configuration.")
        root.quit()
    except Exception as e:
        messagebox.showerror("Connection Error", f"An unexpected error occurred: {e}")
        root.quit()

def on_closing():
    """Handles proper shutdown when the window is closed."""
    global connected, client_socket
    if connected and client_socket:
        try:
            
            client_socket.shutdown(socket.SHUT_RDWR) 
            client_socket.close()
        except:
            pass
    connected = False
    root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title(f"Global Chatroom - {client_name}") 
    root.geometry("800x600")
    root.configure(bg="#282c34")

    chat_display = scrolledtext.ScrolledText(root, state='disabled', wrap='word', 
                                             bg="#1e2125", fg="#abb2bf", font=("Arial", 10),
                                             insertbackground="white", padx=10, pady=10)
    chat_display.pack(padx=10, pady=10, fill="both", expand=True)

    chat_display.tag_config("system_message", foreground="#61afef", font=("Arial", 10, "italic"))
    chat_display.tag_config("my_message", foreground="#98c379", font=("Arial", 10, "bold"))
    

    
    input_frame = tk.Frame(root, bg="#282c34")
    input_frame.pack(padx=10, pady=(0, 10), fill="x")

    message_entry = tk.Entry(input_frame, bg="#3a3f4b", fg="#abb2bf", font=("Arial", 10), 
                              insertbackground="#abb2bf", relief="flat")
    message_entry.pack(side="left", fill="x", expand=True, ipady=5)
    message_entry.bind("<Return>", lambda event: send_message(message_entry, chat_display)) # Bind Enter key

    send_button = tk.Button(input_frame, text="Send", font=("Arial", 10, "bold"), 
                            bg="#61afef", fg="#ffffff", activebackground="#528fc7", 
                            activeforeground="#ffffff", relief="flat", padx=10, 
                            command=lambda: send_message(message_entry, chat_display))
    send_button.pack(side="right", padx=(5,0))

    
    root.protocol("WM_DELETE_WINDOW", on_closing)

    connect_to_server(root, chat_display)
    
    if client_name:
        root.title(f"Global Chatroom - {client_name}")

    root.mainloop()