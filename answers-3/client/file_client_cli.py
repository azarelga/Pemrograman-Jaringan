import os
import socket
import json
import base64
import logging

server_address = ("0.0.0.0", 7777)


def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning("sending message ")
        sock.sendall(command_str.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received = ""  # empty string
        while True:
            # socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(16)
            if data:
                # data is not empty, concat with previous content
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # no more data, stop the process by break
                break
        # at this point, data_received (string) will contain all data coming from the socket
        # to be able to use the data_received as a dict, need to load it using json.loads()
        hasil = json.loads(data_received)
        logging.warning("data received from server:")
        return hasil
    except Exception as e:
        logging.warning(f"error during data receiving: {e}")
        return False


def remote_upload(filename=""):
    command_str = f"UPLOAD {filename}"
    try:
        with open(filename, "rb") as fp:
            isifile = base64.b64encode(fp.read()).decode()
    except:
        print(f"[ERROR] tidak ada file bernama {filename}!")
        return False
    filename = os.path.basename(filename)
    command_str = f"UPLOAD {filename} {isifile}\r\n\r\n"
    hasil = send_command(command_str)
    if hasil["status"] == "OK":
        print(hasil)
        return True
    else:
        print("Gagal")
        print(hasil)
        return False


def remote_delete(filename=""):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if hasil["status"] == "OK":
        return True
    else:
        print("Gagal")
        return False


def remote_list():
    command_str = "LIST"
    hasil = send_command(command_str)
    if hasil["status"] == "OK":
        print("daftar file : ")
        for nmfile in hasil["data"]:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False


def remote_get(filename=""):
    command_str = "GET {filename}"
    hasil = send_command(command_str)
    if hasil["status"] == "OK":
        # proses file dalam bentuk base64 ke bentuk bytes
        namafile = hasil["data_namafile"]
        isifile = base64.b64decode(hasil["data_file"])
        fp = open(namafile, "wb+")
        fp.write(isifile)
        fp.close()
        return True
    else:
        print("Gagal")
        return False


if __name__ == "__main__":
    server_address = ("172.16.16.101", 6969)
    while True:
        cmd = input().split(" ")
        if cmd[0] == "GET":
            if len(cmd) < 2:
                print("[ERROR] no filename provided!")
                continue
            remote_get(cmd[1])
        elif cmd[0] == "LIST":
            remote_list()
        elif cmd[0] == "DELETE":
            remote_delete(cmd[1])
        elif cmd[0] == "UPLOAD":
            remote_upload(cmd[1])
        else:
            print("[ERROR] invalid commands!")
