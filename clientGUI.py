import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk

from client import FileClient


class FileClientGUI:
    def __init__(self):
        self.client = FileClient(log_callback=self.log)
        self.path = None
        self.files = None

        self.root = tk.Tk()
        self.root.title("P2P Client GUI")

        # Hostname Frame
        self.hostname_frame = ttk.Frame(self.root)
        self.hostname_frame.pack_forget()

        hostname_label = ttk.Label(self.hostname_frame, text="Hostname:")
        hostname_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.hostname_entry = ttk.Entry(self.hostname_frame)
        self.hostname_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        init_hostname_button = ttk.Button(
            self.hostname_frame, text="Submit", command=self.init_hostname
        )
        init_hostname_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # Path Frame
        self.path_frame = ttk.Frame(self.root)
        self.path_frame.pack(padx=10, pady=10, side=tk.TOP)

        path_label = ttk.Label(self.path_frame, text="Choose Path:")
        path_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.path_button = ttk.Button(
            self.path_frame, text="Browse", command=self.init_path
        )
        self.path_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # Log Box
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10, side=tk.BOTTOM)

        self.log_frame = ttk.Frame(self.main_frame)
        self.log_frame.pack(side=tk.LEFT)

        label_log = ttk.Label(self.log_frame, text="Logs")
        label_log.pack(pady=10)

        self.log_box = scrolledtext.ScrolledText(
            self.log_frame, wrap=tk.WORD, width=60, height=20, state=tk.DISABLED
        )
        self.log_box.pack(padx=10, pady=10, side=tk.LEFT, expand=True)

        self.repo_frame = ttk.Frame(self.main_frame)
        self.repo_frame.pack_forget()

        self.label_repo = ttk.Label(self.repo_frame, text="My Repository")
        self.label_repo.pack(pady=10)

        self.repo_box = scrolledtext.ScrolledText(
            self.repo_frame,
            wrap=tk.WORD,
            width=60,
            height=20,
            state=tk.DISABLED,
            bg="white",
            fg="black",
        )
        self.repo_box.pack(padx=10, pady=10, side=tk.RIGHT, expand=True)

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

        browse_button = ttk.Button(
            self.commands_frame, text="Browse", command=self.browse_file
        )
        browse_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # New Entry for the second argument (file name)
        self.file_name_entry = ttk.Entry(self.commands_frame)
        self.file_name_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        publish_button = ttk.Button(
            self.commands_frame, text="Publish", command=self.publish
        )
        publish_button.grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)

        # Fetch Section
        fetch_label = ttk.Label(self.commands_frame, text="Fetch:")
        fetch_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.fetch_entry = ttk.Entry(self.commands_frame)
        self.fetch_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        fetch_button = ttk.Button(self.commands_frame, text="Fetch", command=self.fetch)
        fetch_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

        # Quit Button
        quit_button = ttk.Button(
            self.commands_frame, text="Quit", command=self.quit_client
        )
        quit_button.grid(row=2, column=0, columnspan=5, pady=10)

    def init_path(self):
        path = filedialog.askdirectory()
        if path != "":
            self.client.path = path
            self.path_frame.pack_forget()
            self.files = {
                file: False
                for file in os.listdir(self.client.path)
                if os.path.isfile(os.path.join(self.client.path, file))
            }
            self.hostname_frame.pack(padx=10, pady=10, side=tk.TOP)

    def init_hostname(self):
        hostname = self.hostname_entry.get()
        if hostname:
            try:
                client_address = self.client.login(hostname)
                self.log(f"Client address: {client_address}")
                if client_address:
                    self.log(f"Hostname '{hostname}' set successfully.")
                    # threading.Thread(target=self.client.start,
                    # args=(client_address,)).start()
                    self.client.start(client_address)
                    # Show the main commands frame
                    self.hostname_frame.pack_forget()
                    self.commands_frame.pack(side=tk.BOTTOM, expand=True)
                    self.main_frame.pack(side=tk.TOP)
                    self.repo_frame.pack(side=tk.RIGHT)
                    self.process_file(first_time=True)
            except Exception as e:
                self.log(f"Error setting hostname: {e}")
        else:
            self.log("Hostname cannot be empty.")

    def browse_file(self):
        file_path = filedialog.askopenfilename(initialdir=self.client.path)
        if file_path != "":
            if os.path.dirname(file_path) == self.client.path:
                self.file_path_entry.config(state="normal")
                self.file_path_entry.delete(0, tk.END)
                self.file_path_entry.insert(0, file_path)
                self.file_path_entry.config(state="disabled")
            else:
                self.log(f"Choose file in the {self.client.path} directory!")

    def publish(self):
        file_path = self.file_path_entry.get()
        local_name = file_path.split("/")[-1]  # Extracting the file name
        file_name = self.file_name_entry.get()  # Get the second argument (file name)
        if not file_name or not local_name:
            self.log("Error publishing file: Please fill in the blank!")
            return
        try:
            publish_status = self.client.publish(
                self.client.client_socket, local_name, file_name
            )
            if publish_status:
                self.file_path_entry.config(state=tk.NORMAL)
                self.file_path_entry.delete(0, tk.END)
                self.file_path_entry.config(state=tk.DISABLED)
                self.file_name_entry.delete(0, tk.END)
        except Exception as e:
            self.log(f"Error publishing file: {e}")

    def fetch(self):
        file_name = self.fetch_entry.get()
        if not file_name:
            self.log("Error fetching file: File name cannot be blank!")
            return
        try:
            self.client.fetch(self.client.client_socket, file_name)
            self.fetch_entry.delete(0, tk.END)
        except Exception as e:
            self.log(f"Error fetching file: {e}")

    def quit_client(self):
        self.client.quit(self.client.client_socket)
        self.root.destroy()

    def log(self, message):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def process_file(self, first_time=False):
        if self.client.path is not None:
            new_files = [
                file
                for file in list(self.client.local_files.keys())
                if self.files[file] is False
            ]
            dir_unchange = list(self.files.keys()) == [
                file
                for file in os.listdir(self.client.path)
                if os.path.isfile(os.path.join(self.client.path, file))
            ]
            publish_unchange = (
                len(list(self.client.local_files.keys())) == 0 or len(new_files) == 0
            )

            if first_time is True or dir_unchange is False or publish_unchange is False:
                self.repo_box.config(state=tk.NORMAL)
                self.repo_box.delete("1.0", tk.END)
                self.files = {
                    file: False
                    for file in os.listdir(self.client.path)
                    if os.path.isfile(os.path.join(self.client.path, file))
                }

                self.repo_box.insert(
                    tk.END, f"Current directory: {self.client.path}\r\n"
                )

                all_files = list(self.files.keys())
                all_files.sort()
                for file in all_files:
                    if (
                        file in self.client.local_files
                        and self.client.local_files[file] is not None
                    ):
                        self.repo_box.insert(
                            tk.END,
                            f"\n{file[:25] + '...' if len(file) > 25 else file} - "
                            "{self.client.local_files[file]}",
                        )
                        self.files[file] = True
                    else:
                        self.repo_box.insert(
                            tk.END,
                            f"\n{file[:35] + '...' if len(file) > 35 else file} "
                            "(not published)",
                        )
                self.repo_box.config(state=tk.DISABLED)

        self.root.after(5000, self.process_file)


if __name__ == "__main__":
    gui = FileClientGUI()
    gui.root.mainloop()
