import base64
import pandas as pd
import time
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import logging
import os
import socket

server_address = ("0.0.0.0", 7777)


def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning("sending message ")
        command_str += "\r\n\r\n"
        sock.sendall(command_str.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received = ""  # empty string
        while True:
            # socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(65536)
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
        if data_received.endswith("\r\n\r\n"):
            data_received = data_received[:-4]
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
    except Exception as e:
        logging.warning(f"no directory named {filename}: {e}")
        return False
    filename = os.path.basename(filename)
    command_str = f"UPLOAD {filename} {isifile}"
    hasil = send_command(command_str)
    if hasil["status"] == "OK":
        checksum = hashlib.md5(base64.b64decode(isifile)).hexdigest()
        if hasil["checksum"] == checksum:
            print("file integrity safe!")
            return True
        else:
            print("file integrity corrupted!")
            return False
    else:
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
        logging.warning(hasil)
        return False


def remote_get(filename=""):
    command_str = f"GET {filename}"
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
        logging.warning(hasil)
        return False


def worker_task(worker_id, task, dict_file, volume_file):
    print(f" [CLIENT-{worker_id + 1}] STARTED.")
    try:
        if task == 0:
            result = remote_get(dict_file[volume_file])
        elif task == 2:
            result = remote_list()
        else:
            result = remote_upload(dict_file[volume_file])
    except ConnectionError as e:
        logging.warning(f"[CLIENT-{worker_id + 1}] server unreachable: {e}")
        result = False
    print(f"[CLIENT {worker_id + 1}] FINISHED: {'SUCCESS' if result else 'FAIL'}")
    return result


def stress_test(num_worker=1, volume_file=10, task=1, server_worker_pool=0, nomor=0):
    dict_file = {
        "10": "random_10mb.bin",
        "50": "random_50mb.bin",
        "100": "random_100mb.bin",
    }
    catat_awal = time.perf_counter()

    # Simulate success/failure counts for demonstration
    client_success = 0
    client_fail = 0
    server_success = 0
    server_fail = 0

    with ProcessPoolExecutor(num_worker) as executor:
        futures = [
            executor.submit(worker_task, i, task, dict_file, volume_file)
            for i in range(num_worker)
        ]
        for future in futures:
            result = future.result()
            if result:
                client_success += 1
                server_success += 1
            else:
                server_fail += 1
                client_fail += 1

    catat_akhir = time.perf_counter()
    selesai = round(catat_akhir - catat_awal, 2)

    # Throughput: total data transferred / total time
    total_data_mb = int(volume_file) * num_worker
    throughput = total_data_mb / selesai if selesai > 0 else 0

    operasi = "download" if task == 0 else "upload"
    log_row = {
        "Nomor": nomor,
        "Operasi": operasi,
        "Volume": volume_file,
        "Jumlah client worker pool": num_worker,
        "Jumlah server worker pool": server_worker_pool,
        "Waktu total per client": selesai,
        "Throughput per client": throughput,
        "Jumlah worker client yang sukses": client_success,
        "Jumlah worker client yang gagal": client_fail,
        "Jumlah worker server yang sukses": server_success,
        "Jumlah worker server yang gagal": server_fail,
    }
    return log_row


if __name__ == "__main__":
    server_address = ("172.16.16.101", 6969)
    column = [
        "Nomor",
        "Operasi",
        "Volume",
        "Jumlah client worker pool",
        "Jumlah server worker pool",
        "Waktu total per client",
        "Throughput per client",
        "Jumlah worker client yang sukses",
        "Jumlah worker client yang gagal",
        "Jumlah worker server yang sukses",
        "Jumlah worker server yang gagal",
    ]

    if os.path.exists("stress_test_log_process.csv"):
        df = pd.read_csv("stress_test_log_process.csv")
        ops = df["Nomor"].max() + 1
    else:
        df = pd.DataFrame(columns=column)
        ops = 1

    # Task
    # Upload Download = 2
    # 10, 50, 100 MB = 3
    # 1, 5, 50 Clients = 3
    # 1, 5, 50 Servers = 3
    # 2 * 3 * 3 * 3 = 54
    server_worker_pool = int(input("num server workers: "))
    for task in [0]:
        for vol in ["10", "50", "100"]:
            for num in [1, 5, 50]:
                print(f"""
                Stress test with: {"Upload" if task else "Download"} task, {num} workers, {vol}MB file...
                """)
                exists = (
                    (df["Operasi"] == ("download" if task == 0 else "upload"))
                    & (df["Volume"] == int(vol))
                    & (df["Jumlah client worker pool"] == num)
                    & (df["Jumlah server worker pool"] == server_worker_pool)
                ).any()
                if exists:
                    print(
                        "This test configuration has already been conducted. Skipping."
                    )
                    continue
                try:
                    log_row = stress_test(num, vol, task, server_worker_pool, nomor=ops)
                    logging.warning("Log added:")
                    logging.warning(log_row)
                    df.loc[len(df)] = log_row
                    df.to_csv("stress_test_log_process.csv", index=False)
                    ops += 1
                except Exception as e:
                    logging.warning(f"error during stress test: {e}")
    print(df)
