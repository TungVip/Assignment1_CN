import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog
import threading
from client import FileClient

class FileClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("File Client GUI")

        self.client = FileClient()

        # Hostname Frame
        self.hostname_frame = ttk.Frame(self.master)
        self.hostname_frame.pack(padx=10, pady=10)

        hostname_label = ttk.Label(self.hostname_frame, text="Hostname:")
        hostname_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.hostname_entry = ttk.Entry(self.hostname_frame)
        self.hostname_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        init_hostname_button = ttk.Button(self.hostname_frame, text="Summit", command=self.init_hostname)
        init_hostname_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # Log Box
        self.log_box = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=60, height=10)
        self.log_box.pack(padx=10, pady=10)

        # Commands Frame (Initially hidden)
        self.commands_frame = ttk.Frame(self.master)
        self.commands_frame.pack(padx=10, pady=10)
        self.commands_frame.grid_remove()

        self.create_commands_widgets()

    def create_commands_widgets(self):
        # Publish Section
        publish_label = ttk.Label(self.commands_frame, text="Publish:")
        publish_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.file_path_entry = ttk.Entry(self.commands_frame, state="readonly")
        self.file_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        browse_button = ttk.Button(self.commands_frame, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        publish_button = ttk.Button(self.commands_frame, text="Publish", command=self.publish)
        publish_button.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        # Fetch Section
        fetch_label = ttk.Label(self.commands_frame, text="Fetch:")
        fetch_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.fetch_entry = ttk.Entry(self.commands_frame)
        self.fetch_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        fetch_button = ttk.Button(self.commands_frame, text="Fetch", command=self.fetch)
        fetch_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

    def init_hostname(self):
        hostname = self.hostname_entry.get()
        if hostname:
            try:
                self.client.init_hostname(self.client.client_socket, hostname)
                self.log(f"Hostname '{hostname}' set successfully.")
                # Show the main commands frame
                self.hostname_frame.pack_forget()
                self.commands_frame.grid()
            except Exception as e:
                self.log(f"Error setting hostname: {e}")
        else:
            self.log("Hostname cannot be empty.")

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        self.file_path_entry.config(state="normal")
        self.file_path_entry.delete(0, tk.END)
        self.file_path_entry.insert(0, file_path)
        self.file_path_entry.config(state="readonly")

    def publish(self):
        file_path = self.file_path_entry.get()
        local_name = file_path.split("/")[-1]  # Extracting the file name
        try:
            self.client.publish(self.client.client_socket, local_name, file_path)
            self.log(f"Published: {local_name}")
        except Exception as e:
            self.log(f"Error publishing file: {e}")

    def fetch(self):
        file_name = self.fetch_entry.get()
        try:
            self.client.fetch(self.client.client_socket, file_name)
        except Exception as e:
            self.log(f"Error fetching file: {e}")

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

def start_client_gui():
    root = tk.Tk()
    app = FileClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    # Start the client GUI in a separate thread
    gui_thread = threading.Thread(target=start_client_gui)
    gui_thread.start()

    # Start the client in the main thread
    client = FileClient()
    client.start()
