import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from file_protocol import FileProtocol

fp = FileProtocol()


def ProcessTheClient(connection):
    try:
        # request
        data = connection.recv(1024)
        request = data.decode().split(" ")[0]
        logging.warning("")

        if request == "UPLOAD":
            # Use a larger buffer size for better performance
            filename = data.decode().split(" ")[1]
            buffer = data.decode().split(" ")[2].encode()
            total_received = len(buffer)
            while True:
                if b"\r\n\r\n" in buffer:
                    break
                data = connection.recv(512 * 1024 * 1024)  # Increased from 32 bytes
                if not data:
                    break
                buffer += data
                total_received += len(data)
                print(f"\rReceived {total_received} bytes", flush=True)
            print()

            if buffer:
                hasil = fp.proses_string(request, filename, buffer.decode())
        else:
            hasil = fp.proses_string(data.decode())

        hasil = hasil + "\r\n\r\n"
        connection.sendall(hasil.encode())
    except Exception as e:
        logging.warning(f"error during client processing: {e}")
    finally:
        connection.close()
    return


def Server(ipaddress="0.0.0.0", port=8885, max_workers=20):
    ipinfo = (ipaddress, port)
    the_clients = []

    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.bind(ipinfo)
    my_socket.listen(1)

    logging.warning(f"server berjalan di ip address {ipinfo}")
    with ThreadPoolExecutor(max_workers) as executor:
        while True:
            connection, client_address = my_socket.accept()
            logging.warning("connection from {}".format(client_address))
            p = executor.submit(ProcessTheClient, connection)
            the_clients.append(p)


def main():
    worker = int(input("num workers: "))
    Server(ipaddress="0.0.0.0", port=6969, max_workers=worker)


if __name__ == "__main__":
    main()
