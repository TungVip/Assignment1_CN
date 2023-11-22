import socket
import threading
import os
import sys
import json
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

        if not command:
            self.log("Server command cannot be blank!")
        elif command_parts[0] == "discover":
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
                self.clients[client_address]["files"].append({"local_name": local_name, "file_name": file_name})
                self.log(f"File '{file_name}' published by {client_address} with local name '{local_name}'")
            else:
                self.log(f"Unknown client {client_address}")

    def fetch(self, client_socket, requesting_client, file_name):
        with self.lock:
            found_client = next(((addr, data["files"]) for addr, data in self.clients.items() if any(file["file_name"] == file_name for file in data["files"])), None)
    
        if found_client:
            addr, files = found_client
            local_name = next(file["local_name"] for file in files if file["file_name"] == file_name)
    
            response_data = {"file_name": file_name, "error": None, "source": {"address": addr, "local_name": local_name}}
            response = json.dumps(response_data)
            client_socket.send(response.encode("utf-8"))
        else:
            response_data = {"file_name": file_name, "error": "No sources found"}
            response = json.dumps(response_data)
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
                    response_data = {"status": "success", "message": f"Hostname '{hostname}' set for {client_address}", "hostname": hostname, "address": client_address}
                    response = json.dumps(response_data)
                    self.log(response_data["message"])
                    client_socket.send(response.encode("utf-8"))
                else:
                    response_data = {"status": "error", "message": f"Hostname '{hostname}' is already in use.", "hostname": None, "address": None}
                    response = json.dumps(response_data)
                    self.log(response_data["message"])
                    client_socket.send(response.encode("utf-8"))
            else:
                response_data = {"status": "error", "message": f"Unknown client {client_address}", "hostname": None, "address": None}
                response = json.dumps(response_data)
                self.log(response_data["message"])
                client_socket.send(response.encode("utf-8"))

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
            found_clients = {addr: data["files"] for addr, data in self.clients.items() if data["hostname"] == hostname}

        if found_clients:
            for client_address in found_clients:
                response_data = self.send_ping(client_address)
                self.log(response_data)

    def send_ping(self, client_address):
        with self.lock:
            if client_address in self.clients:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    client_socket.connect(client_address)
                    ping_message = {"type": "ping", "error": None}
                    client_socket.send(json.dumps(ping_message).encode("utf-8"))

                    response_data = client_socket.recv(1024).decode("utf-8")
                    return f"Ping response from {client_address}: {response_data}"
                except Exception as e:
                    return f"Error pinging {client_address}: {e}"
                finally:
                    client_socket.close()
            else:
                return f"Unknown client {client_address}"

    def shutdown(self):
        self.log("Shutting down the server...")
        self.is_running = False
        sys.exit(0)

# if __name__ == "__main__":
#     server = FileServer("localhost", 5555)
#     server.start()
