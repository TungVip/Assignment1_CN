import socket
import threading
import os
import sys

class FileServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}  # {client_address: {"hostname": hostname, "files": [list of files]}}
        self.lock = threading.Lock()  # To synchronize access to shared data
        self.is_running = True  # Flag to control server running state

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()

        print(f"Server listening on {self.host}:{self.port}")

        threading.Thread(target=self.command_line_interface).start()

        while self.is_running:
            client_socket, client_address = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

    def command_line_interface(self):
        while self.is_running:
            command = input("Enter server command: ")
            self.process_server_command(command)

    def handle_client(self, client_socket, client_address):
        with self.lock:
            self.clients[client_address] = {"hostname": None, "files": []}

        print(f"New connection from {client_address}")

        # Receive the client's hostname
        # self.set_hostname(client_socket, client_address)

        while True:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break

                self.process_command(client_socket, client_address, data)

            except Exception as e:
                print(f"Error handling client {client_address}: {e}")
                break

        with self.lock:
            if client_address in self.clients:
                del self.clients[client_address]
            if client_socket:
                client_socket.close()
            print(f"Connection from {client_address} closed")

    def process_command(self, client_socket, client_address, command):
        command_parts = command.split()

        if command_parts[0] == "publish":
            self.publish(client_address, command_parts[1], command_parts[2])
        elif command_parts[0] == "fetch":
            self.fetch(client_socket, client_address, command_parts[1])
        elif command_parts[0] == "quit":
            self.quit(client_socket, client_address)
        elif command_parts[0] == "hostname":
            self.set_hostname(client_address, command_parts[1])
        else:
            print(f"Unknown command from {client_address}: {command}")

    def process_server_command(self, command):
        command_parts = command.split()

        if command_parts[0] == "discover":
            self.server_discover(command_parts[1])
        elif command_parts[0] == "ping":
            self.server_ping(command_parts[1])
        elif command_parts[0] == "shutdown":
            self.shutdown()
        else:
            print(f"Unknown server command: {command}")

    def publish(self, client_address, local_name, file_name):
        with self.lock:
            if client_address in self.clients:
                self.clients[client_address]["files"].append(file_name)
                print(f"File '{file_name}' published by {client_address}")
            else:
                print(f"Unknown client {client_address}")

    def fetch(self, client_socket, requesting_client, file_name):
        with self.lock:
            found_clients = [addr for addr, data in self.clients.items() if file_name in data["files"]]

        if found_clients:
            response = f"Available sources for '{file_name}': {', '.join(str(addr) for addr in found_clients)}"
            client_socket.send(response.encode("utf-8"))
        else:
            response = f"No sources found for '{file_name}'"
            client_socket.send(response.encode("utf-8"))

    def quit(self, client_socket, client_address):
        # with self.lock:
        #     if client_address in self.clients:
        #         del self.clients[client_address]
        #     if client_socket:
        #         client_socket.close()
        #     print(f"Connection from {client_address} closed")
        print(f"The client {client_address} has quitted")

    def set_hostname(self, client_address, hostname):
        with self.lock:
            if client_address in self.clients:
                if not any(data["hostname"] == hostname for addr, data in self.clients.items() if addr != client_address):
                    self.clients[client_address]["hostname"] = hostname
                    print(f"Hostname '{hostname}' set for {client_address}")
                else:
                    print(f"Hostname '{hostname}' is already in use.")
            else:
                print(f"Unknown client {client_address}")

    def server_discover(self, hostname):
        with self.lock:
            found_clients = {addr: data["files"] for addr, data in self.clients.items() if data["hostname"] == hostname}

        if found_clients:
            response = f"Files on hosts with hostname '{hostname}': {found_clients}"
        else:
            response = f"No hosts found with hostname '{hostname}'"

        print(response)

    def server_ping(self, hostname):
        with self.lock:
            found_clients = [addr for addr, data in self.clients.items() if data["hostname"] == hostname]

        if found_clients:
            response = f"Hosts with hostname '{hostname}' are online: {', '.join(str(addr) for addr in found_clients)}"
        else:
            response = f"No hosts found with hostname '{hostname}'"

        print(response)

    def shutdown(self):
        print("Shutting down the server...")
        self.is_running = False
        sys.exit(0)

if __name__ == "__main__":
    server = FileServer("localhost", 5555)
    server.start()
