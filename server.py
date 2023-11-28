import json
import select
import socket
import sys
import threading
import time


class FileServer:
    def __init__(self, host, port, log_callback=None, log_request_callback=None):
        self.host = host
        self.port = port
        self.clients = (
            {}
        )  # {client_address: {"hostname": hostname, "files": [list of files]}}
        self.lock = threading.Lock()  # To synchronize access to shared data
        self.is_running = False  # Flag to control server running state
        self.log_callback = log_callback
        self.log_request_callback = log_request_callback

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def log_request(self, message):
        if self.log_request_callback:
            self.log_request_callback(message)
        else:
            print(message)

    def start(self):
        server_thread = threading.Thread(target=self.run_server)
        server_thread.start()

    def run_server(self):
        with self.lock:
            if self.is_running:
                self.log("Server is already running!")
                return
            else:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((self.host, self.port))
                server_socket.listen(5)

                self.is_running = True
                self.log(f"Server listening on {self.host}:{self.port}")

        while self.is_running:
            try:
                client_socket, client_address = server_socket.accept()
                threading.Thread(
                    target=self.handle_client,
                    daemon=True,
                    args=(client_socket, client_address),
                ).start()
            except OSError as e:
                # Check if the error is due to stopping the server, ignore otherwise
                if not self.is_running:
                    break
                else:
                    self.log(f"Error accepting connection: {e}")

    def handle_client(self, client_socket, client_address):
        with self.lock:
            self.clients[client_address] = {
                "hostname": None,
                "status": "online",
                "files": {},
            }

        if self.is_running:
            self.log(f"New connection from {client_address}")

        while self.clients[client_address]["status"] == "online" and self.is_running:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break

                try:
                    data = json.loads(data)
                except Exception as e:
                    self.log(f"Error receiving command: {e}")

                self.process_command(client_socket, client_address, data)

            except Exception as e:
                if self.clients[client_address]["status"] == "offline":
                    break
                self.log(f"Error handling client {client_address}: {e}")
                break

        with self.lock:
            if client_address in self.clients:
                del self.clients[client_address]
            if client_socket:
                client_socket.close()
            if self.is_running:
                self.log(f"Connection from {client_address} closed")

    def process_command(self, client_socket, client_address, command):
        with self.lock:
            if command["header"] == "publish":
                self.log_request(
                    f">>> Client {client_address}: {command['header'].upper()}\n---\n"
                )
                self.publish(
                    client_address,
                    command["payload"]["lname"],
                    command["payload"]["fname"],
                )
            elif command["header"] == "fetch":
                self.log_request(
                    f">>> Client {client_address}: {command['header'].upper()}\n---\n"
                )
                self.fetch(client_socket, client_address, command["payload"]["fname"])
            elif command["header"] == "quit":
                self.log_request(
                    f">>> Client {client_address}: {command['header'].upper()}\n---\n"
                )
                self.quit(client_socket, client_address)
            elif command["header"] == "sethost":
                self.log_request(
                    f">>> Client {client_address}: {command['header'].upper()}\n---\n"
                )
                self.set_hostname(
                    client_socket, client_address, command["payload"]["hostname"]
                )
            else:
                self.log_request(
                    f">>> Client {client_address}: Unknown command {command}"
                )

    def process_server_command(self, command):
        with self.lock:
            if self.is_running:
                command_parts = command.split()
                self.log(f"\nServer$ {command}")

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
            else:
                self.log("Start the server before sending commands!")

    def publish(self, client_address, lname, fname):
        if client_address in self.clients:
            self.clients[client_address]["files"].append(
                {"lname": lname, "fname": fname}
            )
            self.log(
                f"File '{fname}' published by {client_address} with local name '{lname}'"
            )
        else:
            self.log(f"Unknown client {client_address}")

    def fetch(self, client_socket, requesting_client, fname):
        found_client = next(
            (
                (addr, data["files"])
                for addr, data in self.clients.items()
                if any(file["fname"] == fname for file in data["files"])
            ),
            None,
        )

        if found_client:
            addr, files = found_client
            lname = next(file["fname"] for file in files if file["fname"] == fname)

            response_data = {
                "header": "fetch",
                "type": 1,
                "payload": {
                    "success": True,
                    "message": f"File '{fname}' found",
                    "fname": fname,
                    "lname": lname,
                    "available_clients": [
                        {
                            "hostname": data["hostname"],
                            "address": addr,
                        }
                        for addr, data in self.clients.items()
                        if addr != requesting_client
                    ],
                },
            }
            response = json.dumps(response_data)
            client_socket.send(response.encode("utf-8"))
        else:
            response_data = {
                "header": "fetch",
                "type": 1,
                "payload": {
                    "success": False,
                    "message": f"File '{fname}' not found",
                    "fname": fname,
                    "available_clients": [],
                },
            }
            response = json.dumps(response_data)
            client_socket.send(response.encode("utf-8"))

    def quit(self, client_socket, client_address):
        client = self.clients[client_address]
        client.update({"status": "offline"})
        #     if client_address in self.clients:
        #         del self.clients[client_address]
        if client_socket:
            client_socket.close()
        #     print(f"Connection from {client_address} closed")
        self.log(f"The client {client_address} has quitted")

    def set_hostname(self, client_socket, client_address, hostname: str):
        if client_address in self.clients:
            if " " in hostname:
                response = json.dumps(
                    {
                        "header": "sethost",
                        "type": 1,
                        "payload": {
                            "success": False,
                            "message": "Hostname cannot contain spaces",
                            "hostname": hostname,
                            "address": client_address,
                        },
                    }
                )
                client_socket.send(response.encode("utf-8"))
            else:
                if not any(
                    data["hostname"] == hostname
                    for addr, data in self.clients.items()
                    if addr != client_address
                ):
                    self.clients[client_address]["hostname"] = hostname
                    response_data = {
                        "header": "sethost",
                        "type": 1,
                        "payload": {
                            "success": True,
                            "message": f"Hostname '{hostname}' set for {client_address}",
                            "hostname": hostname,
                            "address": client_address,
                        },
                    }
                    response = json.dumps(response_data)
                    self.log(response_data["payload"]["message"])
                    client_socket.send(response.encode("utf-8"))
                else:
                    response_data = {
                        "header": "sethost",
                        "type": 1,
                        "payload": {
                            "success": False,
                            "message": f"Hostname '{hostname}' already in use",
                            "hostname": hostname,
                            "address": client_address,
                        },
                    }
                    response = json.dumps(response_data)
                    self.log(response_data["payload"]["message"])
                    client_socket.send(response.encode("utf-8"))
        else:
            response_data = {
                "header": "sethost",
                "type": 1,
                "payload": {
                    "success": False,
                    "message": f"Unknown client {client_address}",
                    "hostname": hostname,
                    "address": client_address,
                },
            }
            response = json.dumps(response_data)
            self.log(response_data["payload"]["message"])
            client_socket.send(response.encode("utf-8"))

    def server_discover(self, hostname):
        found_clients = {
            addr: data["files"]
            for addr, data in self.clients.items()
            if data["hostname"] == hostname
        }

        if found_clients:
            response = f"Files on hosts with hostname '{hostname}': {found_clients}"
        else:
            response = f"No hosts found with hostname '{hostname}'"

        self.log(response)

    def server_ping(self, hostname):
        found_clients = {
            addr: data["files"]
            for addr, data in self.clients.items()
            if data["hostname"] == hostname
        }

        if found_clients:
            for client_address in found_clients:
                self.log(f"Pinging {hostname}...")
                response_data = self.send_ping(client_address)
                self.log(response_data)
        else:
            self.log(f"Unknown client '{hostname}'")

    def send_ping(self, client_address):
        if client_address in self.clients:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect(client_address)
                ping_message = {"header": "ping", "type": 0}
                start_time = time.time()
                client_socket.send(json.dumps(ping_message).encode("utf-8"))

                ready, _, _ = select.select([client_socket], [], [], 8.0)

                if ready:
                    client_socket.recv(1024).decode("utf-8")
                    end_time = time.time()
                    return (
                        f"Client status: Alive\n"
                        f"RTT: {(end_time - start_time) * 1000} miliseconds"
                    )
                else:
                    return f"Client status: Not Alive\nRTT: None"
            except Exception as e:
                return f"Error pinging client: {e}"
            finally:
                client_socket.close()
        else:
            return f"Unknown client {client_address}"

    def shutdown(self):
        self.log("Shutting down the server...")
        self.is_running = False
        try:
            # Create a dummy connection to unblock the server from accept, and then close the server socket
            dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dummy_socket.connect((self.host, self.port))
            dummy_socket.close()
        except Exception as e:
            if self.is_running:
                self.log(f"Error shutdown the server: {e}")
        sys.exit(0)


# if __name__ == "__main__":
#     server = FileServer("localhost", 5555)
#     server.start()
