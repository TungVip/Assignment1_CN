import socket
import threading
import os
import sys
import tkinter as tk
from tkinter import scrolledtext

class FileServer:
    def __init__(self, host, port, log_callback=None):
        self.host = host
        self.port = port
        self.clients = {}  # {client_address: {"hostname": hostname, "files": [list of files]}}
        self.lock = threading.Lock()  # To synchronize access to shared data
        self.is_running = True  # Flag to control server running state
        self.log_callback = log_callback

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()

        self.log(f"Server listening on {self.host}:{self.port}")

        while self.is_running:
            client_socket, client_address = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

    def handle_client(self, client_socket, client_address):
        with self.lock:
            self.clients[client_address] = {"hostname": None, "files": []}

        self.log(f"New connection from {client_address}")

        while True:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break

                self.process_command(client_socket, client_address, data)

            except Exception as e:
                self.log(f"Error handling client {client_address}: {e}")
                break

        with self.lock:
            if client_address in self.clients:
                del self.clients[client_address]
            if client_socket:
                client_socket.close()
            self.log(f"Connection from {client_address} closed")

    def process_command(self, client_socket, client_address, command):
        command_parts = command.split()

        if command_parts[0] == "publish":
            self.publish(client_address, command_parts[1], command_parts[2])
        elif command_parts[0] == "fetch":
            self.fetch(client_socket, client_address, command_parts[1])
        elif command_parts[0] == "quit":
            self.quit(client_socket, client_address)
        elif command_parts[0] == "hostname":
            self.set_hostname(client_socket, client_address, command_parts[1])
        else:
            self.log(f"Unknown command from {client_address}: {command}")

    def process_server_command(self, command):
        command_parts = command.split()

        if command_parts[0] == "discover":
            self.server_discover(command_parts[1])
        elif command_parts[0] == "ping":
            self.server_ping(command_parts[1])
        elif command_parts[0] == "shutdown":
            self.shutdown()
        else:
            self.log(f"Unknown server command: {command}")

    def publish(self, client_address, local_name, file_name):
        with self.lock:
            if client_address in self.clients:
                self.clients[client_address]["files"].append(file_name)
                self.log(f"File '{file_name}' published by {client_address}")
            else:
                self.log(f"Unknown client {client_address}")

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
        self.log(f"The client {client_address} has quitted")

    def set_hostname(self, client_socket, client_address, hostname):
        with self.lock:
            if client_address in self.clients:
                if not any(data["hostname"] == hostname for addr, data in self.clients.items() if addr != client_address):
                    self.clients[client_address]["hostname"] = hostname
                    response = f"Hostname '{hostname}' set for {client_address}"
                    self.log(response)
                    client_socket.send(response.encode("utf-8"))
                else:
                    response = f"Hostname '{hostname}' is already in use."
                    self.log(response)
                    client_socket.send(response.encode("utf-8"))
            else:
                self.log(f"Unknown client {client_address}")

    def server_discover(self, hostname):
        with self.lock:
            found_clients = {addr: data["files"] for addr, data in self.clients.items() if data["hostname"] == hostname}

        if found_clients:
            response = f"Files on hosts with hostname '{hostname}': {found_clients}"
        else:
            response = f"No hosts found with hostname '{hostname}'"

        self.log(response)

    def server_ping(self, hostname):
        with self.lock:
            found_clients = [addr for addr, data in self.clients.items() if data["hostname"] == hostname]

        if found_clients:
            response = f"Hosts with hostname '{hostname}' are online: {', '.join(str(addr) for addr in found_clients)}"
        else:
            response = f"No hosts found with hostname '{hostname}'"

        self.log(response)

    def shutdown(self):
        self.log("Shutting down the server...")
        self.is_running = False
        sys.exit(0)

# if __name__ == "__main__":
#     server = FileServer("localhost", 5555)
#     server.start()
