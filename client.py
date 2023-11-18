import socket
import threading
import os
import sys

class FileClient:
    def __init__(self):
        self.server_host = "localhost"
        self.server_port = 5555
        self.local_files = {}  # {file_name: file_path}
        self.lock = threading.Lock()  # To synchronize access to shared data
        self.hostname = None

    def start(self):
        # self.hostname = input("Enter your unique hostname: ")

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.server_host, self.server_port))

        # Send the client's hostname to the server
        self.init_hostname(client_socket)

        threading.Thread(target=self.receive_messages, args=(client_socket,)).start()
        
        # Command-shell interpreter
        while True:
            command = input("Enter command: ")
            if command == "quit":
                self.quit(client_socket)
                break
            self.process_command(client_socket, command)

    def receive_messages(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break

                if data.startswith("Available sources for"):
                    self.handle_fetch_sources(client_socket, data)
                    # print(data)
                else:
                    print(data)

            except Exception as e:
                print(f"Error receiving messages: {e}")
                break

    def init_hostname(self, client_socket):
        self.hostname = input("Enter your unique hostname: ")
        self.send_hostname(client_socket)
        data = client_socket.recv(1024).decode("utf-8")
        if not data:
            return
        while "is already in use." in data:
            print(data)
            self.hostname = input("Enter your unique hostname: ")
            self.send_hostname(client_socket)
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break
            if "set for" in data:
                break

    def process_command(self, client_socket, command):
        command_parts = command.split()

        if command_parts[0] == "publish":
            self.publish(client_socket, command_parts[1], command_parts[2])
        elif command_parts[0] == "fetch":
            self.fetch(client_socket, command_parts[1])
        else:
            print(f"Unknown command: {command}")

    def publish(self, client_socket, local_name, file_name):
        with self.lock:
            self.local_files[file_name] = local_name

        command = f"publish {local_name} {file_name}"
        client_socket.send(command.encode("utf-8"))

    def fetch(self, client_socket, file_name):
        command = f"fetch {file_name}"
        client_socket.send(command.encode("utf-8"))

    def handle_fetch_sources(self, client_socket, data):
        sources_data = data.split(":")[1].strip()
        print(f"{data}")
        print(sources_data)

        # for source_data in sources_data:
        # source_address, source_files = sources_data
        # print(f"Source: {source_address}, Files: {source_files}")

        # Automatically initiate P2P connection to the source
        # target_socket = self.p2p_connect(sources_data)
        # print(target_socket)
        #     if target_socket:
        #         # self.download_file(target_socket, file_name)
        #         target_socket.close()

    def quit(self, client_socket):
        with self.lock:
            command = "quit"
            client_socket.send(command.encode("utf-8"))
            client_socket.close()
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
            print(f"Error connecting to {target_address}: {e}")
            return None

    def download_file(self, target_socket, file_name):
        # Implement file download logic here
        pass

if __name__ == "__main__":
    client = FileClient()
    client.start()
