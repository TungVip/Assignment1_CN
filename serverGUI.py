import tkinter as tk
from tkinter import scrolledtext
import threading
from server import FileServer

class ServerGUI:
    def __init__(self, host, port):
        self.server = FileServer(host, port, log_callback=self.log_message)

        self.root = tk.Tk()
        self.root.title("File Server GUI")

        # Style configuration
        self.root.configure(bg='#6daded')  # Set background color to blue

        self.log_text = scrolledtext.ScrolledText(self.root, width=60, height=20, bg='#ecf0f1', fg='#181f26', font=('Helvetica', 10))
        self.log_text.pack(padx=10, pady=10)

        self.command_entry = tk.Entry(self.root, width=40, bg='#ecf0f1', fg='#181f26', font=('Helvetica', 10))
        self.command_entry.pack(pady=10)

        self.send_command_button = tk.Button(self.root, text="Send Command", command=self.send_command, bg='#2ecc71', fg='#ecf0f1', font=('Helvetica', 10))
        self.send_command_button.pack()

        self.start_button = tk.Button(self.root, text="Start Server", command=self.start_server, bg='#2ecc71', fg='#ecf0f1', font=('Helvetica', 10))
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Stop Server", command=self.stop_server, bg='#e74c3c', fg='#ecf0f1', font=('Helvetica', 10))
        self.stop_button.pack()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_server(self):
        threading.Thread(target=self.server.start).start()
        self.log_message("Server started.")

    def stop_server(self):
        self.log_message("Server stopped.")
        self.server.shutdown()

    def send_command(self):
        command = self.command_entry.get()
        threading.Thread(target=self.server.process_server_command, args=(command,)).start()

    def on_close(self):
        self.server.shutdown()
        self.root.destroy()

    def log_message(self, message):
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.yview(tk.END)

if __name__ == "__main__":
    gui = ServerGUI("localhost", 55555) #192.168.1.247
    gui.root.mainloop()
