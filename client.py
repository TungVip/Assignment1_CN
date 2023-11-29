import json
import os
import socket
import sys
import threading
import traceback


class FileClient:
    def __init__(self, log_callback=None):
        self.server_host = "localhost"
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
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                data = json.loads(client_socket.recv(1024).decode("utf-8", "replace"))
                if not data:
                    break

                if data["header"] == "fetch" and data["payload"] is not None:
                    self.handle_fetch_sources(client_socket, data)
                    # print(data)
                else:
                    self.log(data["payload"]["message"])

            except ConnectionResetError:
                # Handle the case where the server closes the connection
                self.log("Connection closed by the server.")
                break

            except Exception as e:
                if self.stop_threads:
                    break
                self.log(f"Error receiving messages: {e}")
                self.log(f"{traceback.format_exc()}")
                break

    def start_listener(self, client_address):
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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

    def handle_client(self, client_socket: socket.socket, client_address):
        while not self.stop_threads and client_socket.fileno() != -1:
            raw_data = client_socket.recv(1024).decode("utf-8", "replace")
            print(f"This is raw_data received from client fetch request {raw_data}")
            if not raw_data:
                break
            data = json.loads(raw_data)
            print(data)
            if data == {"header": "ping", "type": 0}:
                respond = {
                    "header": "ping",
                    "type": 1,
                    "payload": {"success": True, "message": "pong"},
                }
                client_socket.sendall(json.dumps(respond).encode("utf-8", "replace"))
                client_socket.close()
                break

            if data["header"] == "download":
                self.send_file(client_socket, data["payload"]["fname"])
                client_socket.close()
                break

    def send_file(self, client_socket: socket.socket, fname):
        local_name = [
            file for file in self.local_files if self.local_files[file] == fname
        ][0]
        if not os.path.exists(
            os.path.join(self.path, local_name)
        ) or not os.path.isfile(os.path.join(self.path, local_name)):
            reply = {
                "header": "download",
                "type": 1,
                "payload": {
                    "success": False,
                    "message": f"The file you requested {fname} is not available",
                    "length": None,
                },
            }
            client_socket.sendall(json.dumps(reply).encode("utf-8", "replace"))

        length = os.path.getsize(os.path.join(self.path, local_name))
        reply = {
            "header": "download",
            "type": 1,
            "payload": {
                "success": True,
                "message": f"{fname} is available",
                "length": length,
            },
        }
        binary_reply = json.dumps(reply).encode("utf-8", "replace")

        response_length = (len(binary_reply)).to_bytes(8, "big")
        client_socket.sendall(response_length + binary_reply)
        print(f"currently at sendall file {reply}")
        with open(os.path.join(self.path, local_name), "rb") as file:
            offset = 0
            try:
                while offset < length:
                    data = file.read(1024)
                    offset += len(data)
                    client_socket.sendall(data)
            except ConnectionResetError:
                self.log("Connection closed by peer.")
                return False
            except Exception as e:
                print(f"Error sending file: {e}")
                reply = {
                    "header": "download",
                    "type": 1,
                    "payload": {
                        "success": False,
                        "message": f"{e}",
                        "length": length,
                    },
                }
                client_socket.sendall(json.dumps(reply).encode("utf-8", "replace"))
                return False
        return True

    def init_hostname(self, client_socket, hostname):
        self.hostname = hostname
        self.send_hostname(client_socket)
        data = json.loads(client_socket.recv(1024).decode("utf-8", "replace"))
        if not data:
            return None

        if data["payload"]["success"] is False:
            self.log(data["payload"]["message"])
            return None
        address = data["payload"]["address"]
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

    def publish(self, client_socket, local_name: str, file_name: str):
        # make file_name has the same extension as local_name
        if len(local_name.split(".")) > 0:
            file_name = file_name + "." + local_name.split(".")[-1]

        with self.lock:
            if local_name in self.local_files or file_name in self.local_files.values():
                self.log(
                    f"File with local name '{local_name}'"
                    f" or file name '{file_name}' already exists."
                )
                return False

        # command = f"publish {local_name} {file_name}"
        command = {
            "header": "publish",
            "type": 0,
            "payload": {"lname": local_name, "fname": file_name},
        }
        request = json.dumps(command)
        try:
            client_socket.sendall(request.encode("utf-8", "replace"))
        except Exception as e:
            self.log(f"Error publish file to server: {e}")
            return False

        self.local_files[local_name] = file_name
        self.log(f"Published: '{local_name}' as '{file_name}'")
        return True

    def fetch(self, client_socket, file_name):
        # command = f"fetch {file_name}"
        command = {"header": "fetch", "type": 0, "payload": {"fname": file_name}}
        request = json.dumps(command)
        try:
            client_socket.sendall(request.encode("utf-8", "replace"))
        except Exception as e:
            self.log(f"Error fetch file: {e}")

    def handle_fetch_sources(self, client_socket, data):
        sources_data = data["payload"]
        print(f"{data}")
        print(sources_data)
        fname = sources_data["fname"]
        if not sources_data["success"]:
            self.log("No other clients with the file found!")
            return
        address = sources_data["available_clients"][0]["address"]
        address = (address[0], int(address[1]))

        # Automatically initiate P2P connection to the source
        target_socket = self.p2p_connect(address)
        # print(target_socket)
        if target_socket:
            fetch_status = self.download_file(target_socket, fname)
            if fetch_status is True:
                self.log("Fetch successfully!")
            else:
                self.log("Fetch failed!")
                if os.path.isfile(os.path.join(self.path, fname)):
                    os.remove(os.path.join(self.path, fname))
            target_socket.close()
        else:
            self.log("Fetch failed!")

    def quit(self, client_socket):
        self.stop_threads = True  # Set the flag to stop threads
        with self.lock:
            command = {
                "type": "quit",
            }
            try:
                request = json.dumps(command)
                client_socket.sendall(request.encode("utf-8", "replace"))
            except Exception as e:
                self.log(f"Error connecting to server: {e}")
        client_socket.close()
        if hasattr(self, "listener_socket"):
            self.listener_socket.close()
        print("Client connection closed. Exiting.")
        sys.exit(0)

    def send_hostname(self, client_socket):
        # command = f"hostname {self.hostname}"
        command = {
            "header": "sethost",
            "type": 0,
            "payload": {
                "hostname": self.hostname,
            },
        }
        request = json.dumps(command)
        client_socket.sendall(request.encode("utf-8", "replace"))

    def p2p_connect(self, target_address):
        try:
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # target_socket.connect((target_address, self.server_port))
            target_socket.connect(target_address)
            return target_socket
        except Exception as e:
            self.log(f"Error connecting to {target_address}: {e}")
            return None

    def download_file(self, target_socket: socket.socket, file_name):
        # Implement file download logic here
        data = {
            "header": "download",
            "type": 0,
            "payload": {
                "fname": file_name,
            },
        }
        target_socket.sendall(json.dumps(data).encode("utf-8", "replace"))

        response_length = int.from_bytes(target_socket.recv(8), "big")
        recved_data = target_socket.recv(response_length).decode("utf-8", "replace")

        data = json.loads(recved_data)
        print(f"currently at download file {data}")
        fname = file_name
        if os.path.isfile(os.path.join(self.path, fname)):
            fname = fname.split(".")[0] + "_copy." + fname.split(".")[1]
        length = data["payload"]["length"]
        if data["payload"]["success"] is False:
            self.log(data["payload"]["message"])
            return False

        self.log("Downloading file...")
        with open(os.path.join(self.path, fname), "wb") as file:
            try:
                offset = 0
                while offset < length:
                    recved = target_socket.recv(1024)

                    if not recved:
                        self.log("Connection closed by peer.")
                        return False

                    file.write(recved)
                    offset += 1024
                    self.log(f"Received {offset} bytes of data...")

                self.log("Download completed!")

            except ConnectionResetError:
                self.log("Connection closed by peer.")
                return False
            except Exception as e:
                print(f"Error receiving file: {e}")
                self.log(f"Error receiving file: {e}")
                return False
        return True


# if __name__ == "__main__":
#     client = FileClient()
#     client.start()
