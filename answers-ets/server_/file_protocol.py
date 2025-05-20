import json
import logging
import shlex
from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses 
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat

* data yang masuk dari client adalah dalam bentuk bytes yang 
pada akhirnya akan diproses dalam bentuk string
 
* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""


class FileProtocol:
    def __init__(self):
        self.file = FileInterface()

    def proses_string(self, request, filename="", filecontent=""):
        logging.warning("processing string...")
        if request != "UPLOAD":
            try:
                c = shlex.split(request)
                c_request = c[0].lower().strip()
                params = [x for x in c[1:]]
            except ValueError as e:
                logging.error(f"shlex.split error: {e}")
                return json.dumps(dict(status="ERROR", data="Malformed input string"))
        else:
            c_request = request.lower().strip()
            params = [filename, filecontent]

        logging.warning(f"memproses request: {c_request}")

        try:
            cl = getattr(self.file, c_request)(params)
            logging.warning(f"operasi {c_request} berhasil!")
            return json.dumps(cl)
        except Exception:
            return json.dumps(dict(status="ERROR", data="request tidak dikenali"))


if __name__ == "__main__":
    # contoh pemakaian
    fp = FileProtocol()
    print(fp.proses_string("LIST"))
    print(fp.proses_string("GET pokijan.jpg"))
