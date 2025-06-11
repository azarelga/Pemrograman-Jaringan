from socket import *
import os
import ssl
import socket
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer
import logging

httpserver = HttpServer(logging)


def ProcessTheClient(connection, address):
    try:
        # Step 1: Read headers first
        headers_data = b""
        while True:
            data = connection.recv(1)
            if not data:
                connection.close()
                return
            headers_data += data

            # Check for end of headers
            if headers_data.endswith(b"\r\n\r\n"):
                break

        # Step 2: Parse headers to get Content-Length
        headers_str = headers_data.decode("utf-8")
        header_lines = headers_str.strip().split("\r\n")

        content_length = 0
        for line in header_lines:
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":", 1)[1].strip())
                break

        # Step 3: Read exact body length if Content-Length exists
        # body = ""
        body_data = b""
        if content_length > 0:
            while len(body_data) < content_length:
                remaining = content_length - len(body_data)
                chunk = connection.recv(min(4096, remaining))
                if not chunk:
                    break
                body_data += chunk

        # Process the complete request
        complete_request = headers_data + body_data
        response = httpserver.proses(complete_request)

        if response:
            response = response + "\r\n\r\n".encode("utf-8")
            connection.sendall(response)
            logging.info(f"Response sent to {address}")

        connection.close()

    except Exception as e:
        logging.error(f"Error processing client {address}: {e}")
        connection.close()


def Server():
    the_clients = []
    # ------------------------------
    cert_location = os.path.join(os.path.dirname(__file__), "../certs/")
    cert_location = os.path.abspath(cert_location)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=cert_location + "/domain.crt", keyfile=cert_location + "/domain.key"
    )
    # ---------------------------------
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    port = 80
    my_socket.bind(("0.0.0.0", port))
    my_socket.listen(1)
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Server is listening on port {port}")

    with ThreadPoolExecutor(20) as executor:
        while True:
            connection, client_address = my_socket.accept()
            try:
                p = executor.submit(ProcessTheClient, connection, client_address)
                the_clients.append(p)
                jumlah = [f"\n {i} \n" for i in the_clients if i.running()]
                logging.info(jumlah)
            except ssl.SSLError as e:
                logging.warning(str(e))


def main():
    print("--------------Azarel's HTTP Server 1.0--------------")
    Server()


if __name__ == "__main__":
    main()
