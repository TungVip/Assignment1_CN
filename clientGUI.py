import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog
import threading
from client import FileClient

class FileClientGUI:
    def __init__(self):
        self.client = FileClient(log_callback=self.log)

        self.root = tk.Tk()
        self.root.title("P2P Client GUI")

        # Hostname Frame
        self.hostname_frame = ttk.Frame(self.root)
        self.hostname_frame.pack(padx=10, pady=10)

        hostname_label = ttk.Label(self.hostname_frame, text="Hostname:")
        hostname_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.hostname_entry = ttk.Entry(self.hostname_frame)
        self.hostname_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        init_hostname_button = ttk.Button(self.hostname_frame, text="Submit", command=self.init_hostname)
        init_hostname_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # Log Box
        self.log_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=60, height=10)
        self.log_box.pack(padx=10, pady=10)

        # Commands Frame (Initially hidden)
        self.commands_frame = ttk.Frame(self.root)
        # Use pack for the commands frame
        self.commands_frame.pack_forget()

        self.create_commands_widgets()

    def create_commands_widgets(self):
        # Publish Section
        publish_label = ttk.Label(self.commands_frame, text="Publish:")
        publish_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.file_path_entry = ttk.Entry(self.commands_frame, state="readonly")
        self.file_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        browse_button = ttk.Button(self.commands_frame, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # New Entry for the second argument (file name)
        self.file_name_entry = ttk.Entry(self.commands_frame)
        self.file_name_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        publish_button = ttk.Button(self.commands_frame, text="Publish", command=self.publish)
        publish_button.grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)

        # Fetch Section
        fetch_label = ttk.Label(self.commands_frame, text="Fetch:")
        fetch_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.fetch_entry = ttk.Entry(self.commands_frame)
        self.fetch_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        fetch_button = ttk.Button(self.commands_frame, text="Fetch", command=self.fetch)
        fetch_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

        # Quit Button
        quit_button = ttk.Button(self.commands_frame, text="Quit", command=self.quit_client)
        quit_button.grid(row=2, column=0, columnspan=5, pady=10)

    def init_hostname(self):
        hostname = self.hostname_entry.get()
        if hostname:
            try:
                client_address = self.client.login(hostname)
                if client_address:
                    self.log(f"Hostname '{hostname}' set successfully.")
                    # threading.Thread(target=self.client.start, args=(client_address,)).start()
                    self.client.start(client_address)
                    # Show the main commands frame
                    self.hostname_frame.pack_forget()
                    self.commands_frame.pack()
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
        file_name = self.file_name_entry.get()  # Get the second argument (file name)
        try:
            publish_status = self.client.publish(self.client.client_socket, local_name, file_name)
            if publish_status:
                self.log(f"Published: '{local_name}' as '{file_name}'")
        except Exception as e:
            self.log(f"Error publishing file: {e}")

    def fetch(self):
        file_name = self.fetch_entry.get()
        try:
            self.client.fetch(self.client.client_socket, file_name)
        except Exception as e:
            self.log(f"Error fetching file: {e}")

    def quit_client(self):
        self.client.quit(self.client.client_socket)
        self.root.destroy()

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)


if __name__ == "__main__":
    gui = FileClientGUI()
    gui.root.mainloop()
