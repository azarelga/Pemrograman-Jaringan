import logging
import socket
import threading
from datetime import datetime


class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        try:
            while True:
                data = self.connection.recv(32)
                request_string = data.decode("utf-8")
                if request_string.startswith("TIME") and request_string.endswith("\n"):
                    message = f"JAM {datetime.now().strftime('%H:%M:%S')}\r\n"
                    self.connection.sendall(message.encode("utf-8"))
                elif request_string.startswith("QUIT") and request_string.endswith(
                    "\n"
                ):
                    self.connection.close()
                    break
                else:
                    self.connection.sendall(data)
                    continue
            self.connection.close()
        except Exception as e:
            logging.warning(f"Exception: {e}")
        finally:
            self.connection.close()


class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(("0.0.0.0", 45000))
        self.my_socket.listen(1)

        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.warning(f"connection from {self.client_address}")
            clt = ProcessTheClient(self.connection, self.client_address)
            clt.start()
            self.the_clients.append(clt)


def main():
    svr = Server()
    svr.start()


if __name__ == "__main__":
    main()
