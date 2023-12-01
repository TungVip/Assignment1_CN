# import platform
import threading
import PySimpleGUI as sg

from server import ServerLogic

class ServerGUI:
    def __init__(self, host, port):
        self.server = FileServer(
            host,
            port,
            log_callback=self.log_message,
            log_request_callback=self.log_request,
        )

        # Layout
        layout = [
            [sg.Text("Logs", font=("Helvetica", 24, "bold"))],
            [sg.Multiline("", key="-LOG-", size=(80, 10), disabled=True, autoscroll=True)],
            [sg.Text("Requests", font=("Helvetica", 24, "bold"))],
            [sg.Multiline("", key="-REQUEST_LOG-", size=(60, 10), font=("Helvetica", 14), disabled=True, autoscroll=True)],
            [sg.InputText(key="-COMMAND-", size=(60, 1), font=("Helvetica", 12)),
             sg.Button("Send Command", key="-SEND_COMMAND-")],
            [sg.Button("Start Server", key="-START_SERVER-"),
             sg.Button("Stop Server", key="-STOP_SERVER-")],
        ]

        self.window = sg.Window("P2P Server GUI", layout, finalize=True)

    def start_server(self):
        self.server.start()

    def stop_server(self):
        self.server.shutdown()

    def send_command(self, command):
        threading.Thread(target=self.server.process_server_command, args=(command,)).start()

    def log_message(self, message):
        self.window["-LOG-"].update(value=message + "\n")

    def log_request(self, message):
        self.window["-REQUEST_LOG-"].update(value=message + "\n")

    def run(self):
        while True:
            event, values = self.window.read()

            if event == sg.WIN_CLOSED:
                self.server.shutdown()
                break

            elif event == "-START_SERVER-":
                self.start_server()

            elif event == "-STOP_SERVER-":
                self.stop_server()

            elif event == "-SEND_COMMAND-":
                command = values["-COMMAND-"]
                self.send_command(command)

        self.window.close()

if __name__ == "__main__":
    gui = ServerGUI("localhost", 8888)
    gui.run()
