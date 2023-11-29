import platform
import threading
import tkinter as tk
from tkinter import scrolledtext

from tkmacosx import Button

from server import FileServer


class ServerGUI:
    def __init__(self, host, port):
        self.server = FileServer(
            host,
            port,
            log_callback=self.log_message,
            log_request_callback=self.log_request,
        )

        self.root = tk.Tk()
        self.root.title("P2P Server GUI")

        # Style configuration
        self.root.configure(bg="#6daded")  # Set background color to blue

        self.main_frame = tk.Frame(self.root, bg="#6daded")
        self.main_frame.pack(pady=10, side=tk.TOP)

        self.log_frame = tk.Frame(self.main_frame, bg="#6daded")
        self.log_frame.pack(side=tk.LEFT)

        self.label_log = tk.Label(
            self.log_frame,
            text="Logs",
            bg="#6daded",
            fg="#ecf0f1",
            font=("Helvetica", 24, "bold"),
        )
        self.label_log.pack(pady=10)

        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            width=100,
            state="disabled",
            height=20,
            fg="#ecf0f1",
            bg="#181f26",
            highlightbackground="#6daded",
        )
        self.log_text.pack(padx=10, pady=10)

        self.request_log_frame = tk.Frame(self.main_frame, bg="#6daded")
        self.request_log_frame.pack(side=tk.RIGHT)

        self.label_request_log = tk.Label(
            self.request_log_frame,
            text="Requests",
            bg="#6daded",
            fg="#ecf0f1",
            font=("Helvetica", 24, "bold"),
        )
        self.label_request_log.pack(pady=10)

        self.request_log_text = scrolledtext.ScrolledText(
            self.request_log_frame,
            width=50,
            state="disabled",
            height=20,
            bg="#ecf0f1",
            fg="#181f26",
            highlightbackground="#6daded",
            font=("Helvetica", 14),
        )
        self.request_log_text.pack(padx=10, pady=10)

        self.command_entry = tk.Entry(
            self.root,
            width=60,
            bg="#ecf0f1",
            fg="#181f26",
            highlightbackground="#6daded",
            cursor="xterm",
            font=("Helvetica", 12),
        )
        self.command_entry.pack(pady=10)

        self.send_command_button = Button(
            self.root,
            text="Send Command",
            command=self.send_command,
            bg="#2ECC71",
            fg="#ecf0f1",
            font=("Helvetica", 10),
        )
        self.send_command_button.pack()

        self.start_button = Button(
            self.root,
            text="Start Server",
            command=self.start_server,
            bg="#2ecc71",
            fg="#ecf0f1",
            font=("Helvetica", 10),
        )
        self.start_button.pack(pady=10)

        self.stop_button = Button(
            self.root,
            text="Stop Server",
            command=self.stop_server,
            bg="#e74c3c",
            fg="#ecf0f1",
            font=("Helvetica", 10),
        )
        self.stop_button.pack(pady=20)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_server(self):
        self.log_message("Starting server...")
        self.server.start()

    def stop_server(self):
        self.log_message("Server stopped.")
        self.server.shutdown()

    def send_command(self):
        command = self.command_entry.get()
        threading.Thread(
            target=self.server.process_server_command, args=(command,)
        ).start()

    def on_close(self):
        self.server.shutdown()
        self.root.destroy()

    def log_message(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.yview(tk.END)
        self.log_text.configure(state="disabled")

    def log_request(self, message):
        self.request_log_text.configure(state="normal")
        self.request_log_text.insert(tk.END, message + "\n")
        self.request_log_text.yview(tk.END)
        self.request_log_text.configure(state="disabled")


if __name__ == "__main__":
    gui = ServerGUI("localhost", 2701)  # 192.168.1.247
    gui.root.mainloop()
