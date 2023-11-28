import json
import os
import socket
import sys
import threading


class FileClient:
    def __init__(self, log_callback=None):
        self.server_host = "192.168.43.147"
        self.server_port = 55555
        self.local_files = {}  # {file_name: file_path}
        self.lock = threading.Lock()  # To synchronize access to shared data
        self.hostname = None
        self.path = None
        self.stop_threads = False  # Flag to signal threads to terminate
        self.log_callback = log_callback
        self.client_socket = None

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def login(self, hostname):
        # self.hostname = input("Enter your unique hostname: ")

        if not self.client_socket:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.server_host, self.server_port))
            except Exception as e:
                self.log(f"Error connect to server: {e}")
                self.client_socket = None
                return None

        # Send the client's hostname to the server
        client_address = self.init_hostname(self.client_socket, hostname)

        return client_address

    def start(self, client_address):
        self.receive_messages_thread = threading.Thread(
            target=self.receive_messages, daemon=True, args=(self.client_socket,)
        )
        self.receive_messages_thread.start()

        # Start the listener thread
        self.listener_thread = threading.Thread(
            target=self.start_listener, daemon=True, args=(client_address,)
        )
        self.listener_thread.start()

        # Command-shell interpreter
        # while True:
        #     command = input("Enter command: ")
        #     if command == "quit":
        #         self.quit(client_socket)
        #         break
        #     self.process_command(client_socket, command)

    def receive_messages(self, client_socket):
        while not self.stop_threads:
            try:
                data = json.loads(client_socket.recv(1024).decode("utf-8"))
                if not data:
                    break

                if not data["error"]:
                    self.handle_fetch_sources(client_socket, data)
                    # print(data)
                else:
                    self.log(data)

            except ConnectionResetError:
                # Handle the case where the server closes the connection
                self.log("Connection closed by the server.")
                break

            except Exception as e:
                if self.stop_threads:
                    break
                self.log(f"Error receiving messages: {e}")
                break

    def start_listener(self, client_address):
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener_socket.bind(client_address)
        self.listener_socket.listen()

        while not self.stop_threads:
            try:
                client_socket, addr = self.listener_socket.accept()
                threading.Thread(
                    target=self.handle_client, args=(client_socket, addr)
                ).start()
            except OSError as e:
                # Check if the error is due to stopping threads, ignore otherwise
                if not self.stop_threads:
                    self.log(f"Error accepting connection: {e}")
                    break

    def handle_client(self, client_socket, client_address):
        while not self.stop_threads:
            raw_data = client_socket.recv(1024).decode("utf-8")
            print(f"This is raw_data received from client fetch request {raw_data}")
            if not raw_data:
                break
            data = json.loads(raw_data)
            print(data)
            if data["type"] == "ping":
                client_socket.send(json.dumps({"type": "pong"}).encode("utf-8"))
                client_socket.close()
                break

            status = self.send_file(client_socket, data["local_name"])

    def send_file(self, client_socket, local_name):
        if not os.path.exists(local_name) or not os.path.isfile(local_name):
            reply = {"status": "Error"}
            # reply.update({"status" : "Error"})
            self.socket.send(json.dumps(reply).encode())
            raise FileNotFoundError(f"{local_name} is not available")
        fname = os.path.split(local_name)[-1]
        length = os.path.getsize(local_name)
        reply = {"status": "available", "length": length, "file": fname}
        reply.update({"status": "available", "length": length, "file": fname})
        client_socket.send(json.dumps(reply).encode())
        print(f"currently at send file {reply}")
        with open(local_name, "rb") as file:
            offset = 0
            while offset < length:
                data = file.read(1024)
                offset += len(data)
                client_socket.send(data)
        return True

    def init_hostname(self, client_socket, hostname):
        self.hostname = hostname
        self.send_hostname(client_socket)
        data = json.loads(client_socket.recv(1024).decode("utf-8"))
        if not data:
            return None
        # while data["status"] == "error":
        #     print(data["message"])
        #     self.hostname = input("Enter your unique hostname: ")
        #     self.send_hostname(client_socket)
        #     data = json.loads(client_socket.recv(1024).decode("utf-8"))
        #     if not data:
        #         break
        #     if data["status"] == "success":
        #         break
        if data["status"] == "error":
            self.log(data["message"])
            return None
        address = data["address"]
        address = (address[0], int(address[1]))
        # self.start_listener(address)
        return address

    def process_command(self, client_socket, command):
        command_parts = command.split()

        if command_parts[0] == "publish":
            if command_parts[1] == "" or command_parts[2] == "":
                raise ValueError("filename and localname are required")
            elif not os.path.exists(command_parts[1]):
                raise FileNotFoundError(f"{command_parts[1]} is not available")
            elif not os.path.isfile(command_parts[1]):
                raise FileExistsError(f"{command_parts[1]} is not a file")
            else:
                self.publish(client_socket, command_parts[1], command_parts[2])
        elif command_parts[0] == "fetch":
            self.fetch(client_socket, command_parts[1])
        else:
            print(f"Unknown command: {command}")

    def publish(self, client_socket, local_name, file_name):
        with self.lock:
            if local_name in self.local_files or file_name in self.local_files.values():
                self.log(
                    f"File with local name '{local_name}'"
                    "or file name '{file_name}' already exists."
                )
                return False

            self.local_files[local_name] = file_name

        command = f"publish {local_name} {file_name}"
        client_socket.send(command.encode("utf-8"))

        return True

    def fetch(self, client_socket, file_name):
        command = f"fetch {file_name}"
        client_socket.send(command.encode("utf-8"))

    def handle_fetch_sources(self, client_socket, data):
        sources_data = data["source"]
        print(f"{data}")
        print(sources_data)
        local_name = sources_data["local_name"]
        address = sources_data["address"]
        address = (address[0], int(address[1]))

        # Automatically initiate P2P connection to the source
        target_socket = self.p2p_connect(address)
        # print(target_socket)
        if target_socket:
            fetch_status = self.download_file(target_socket, local_name)
            if fetch_status is True:
                self.log("Fetch successfully!")
            target_socket.close()

    def quit(self, client_socket):
        self.stop_threads = True  # Set the flag to stop threads
        with self.lock:
            command = "quit"
            try:
                client_socket.send(command.encode("utf-8"))
            except Exception as e:
                self.log(f"Error connecting to server: {e}")
        client_socket.close()
        if hasattr(self, "listener_socket"):
            self.listener_socket.close()
        print("Client connection closed. Exiting.")
        sys.exit(0)

    def send_hostname(self, client_socket):
        command = f"hostname {self.hostname}"
        client_socket.send(command.encode("utf-8"))

    def p2p_connect(self, target_address):
        try:
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # target_socket.connect((target_address, self.server_port))
            target_socket.connect(target_address)
            return target_socket
        except Exception as e:
            self.log(f"Error connecting to {target_address}: {e}")
            return None

    def download_file(self, target_socket, local_name):
        # Implement file download logic here
        data = {"type": "CONNECT", "action": "request", "local_name": local_name}
        target_socket.send(json.dumps(data).encode("utf-8"))

        data = json.loads(target_socket.recv(1024).decode())
        print(f"currently at download file {data}")
        fname = data["file"] + "_fetch"
        length = data["length"]
        if data["status"] == "Error":
            raise ConnectionAbortedError("File is not available")
        with open(os.path.join(self.path, fname), "wb") as file:
            offset = 0
            while offset < length:
                recved = target_socket.recv(1024)
                file.write(recved)
                offset += 1024
        return True


# if __name__ == "__main__":
#     client = FileClient()
#     client.start()
