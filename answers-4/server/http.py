import os
import urllib.parse
import os.path
from glob import glob
from datetime import datetime


class HttpServer:
    def __init__(self, logging=None):
        self.sessions = {}
        self.types = {}
        self.types[".pdf"] = "application/pdf"
        self.types[".jpg"] = "image/jpeg"
        self.types[".jpeg"] = "image/jpeg"  # Added for .jpeg
        self.types[".png"] = "image/png"  # Added for .png
        self.types[".txt"] = "text/plain"
        self.types[".html"] = "text/html"
        self.logging = logging
        self.file_serving_root = "./"

    def response(self, kode=404, message="Not Found", messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime("%c")
        resp = []
        resp.append("HTTP/1.0 {} {}\r\n".format(kode, message))
        resp.append("Date: {}\r\n".format(tanggal))
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append("Content-Length: {}\r\n".format(len(messagebody)))
        for kk in headers:
            resp.append("{}:{}\r\n".format(kk, headers[kk]))
        resp.append("\r\n")

        response_headers = ""
        for i in resp:
            response_headers = "{}{}".format(response_headers, i)
        if type(messagebody) is not bytes:
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody

        # response adalah bytes
        return response

    def proses(self, request_data):
        # Split request into headers and body
        if b"\r\n\r\n" in request_data:
            headers_section, body = request_data.split(b"\r\n\r\n", 1)
            headers_section = headers_section.decode("utf-8")
        else:
            headers_section = request_data
            body = ""

        # Split headers into lines
        header_lines = headers_section.split("\r\n")
        request_line = header_lines[0] if header_lines else ""
        headers = header_lines[1:] if len(header_lines) > 1 else []

        j = request_line.split(" ")
        try:
            method = j[0].upper().strip()
            if method == "GET":
                object_address = j[1].strip()
                return self.http_get(object_address, headers)
            elif method == "POST":
                object_address = j[1].strip()
                if object_address.startswith("/upload"):
                    return self.http_upload(object_address, headers, body)
                return self.http_post(object_address, headers, body)
            elif method == "DELETE":
                object_address = j[1].strip()
                return self.http_delete(object_address, headers)
            else:
                return self.response(400, "Bad Request", "", {})
        except (IndexError, ValueError):
            return self.response(400, "Bad Request", "", {})

    def http_get(self, object_address, headers):
        object_address = object_address[1:]
        full_path = os.path.abspath(object_address)
        if os.path.isdir(full_path) or object_address.endswith("/"):
            return self.http_list(object_address, headers)
        elif os.path.isfile(full_path):
            try:
                with open(full_path, "rb") as fp:
                    isi = fp.read()

                fext = os.path.splitext(
                    self.file_serving_root + object_address)[1]
                content_type = self.types.get(fext, "application/octet-stream")

                headers = {}
                headers["Content-type"] = content_type

                return self.response(200, "OK", isi, headers)
            except Exception as e:
                return self.response(500, "Internal Server Error", str(e), {})
        else:
            return self.response(
                404,
                "Not Found",
                f"{object_address} is not found.",
                {"Content-type": "text/plain"},
            )

    def http_post(self, object_address, headers, body):
        # Extract POST body from the original data

        if self.logging:
            self.logging.info(
                f"POST to {object_address} with body: {body[:100]}...")

        response_body = f"Received POST to {object_address}\nBody length: {len(body)} bytes\nBody content:\n{body}"
        return self.response(200, "OK", response_body, {"Content-type": "text/plain"})

    def http_list(self, object_address, headers):
        dir_path = urllib.parse.unquote(object_address)
        dir_path_abs = os.path.abspath(dir_path)
        if not os.path.isdir(dir_path_abs):
            return self.response(
                404,
                "Not Found",
                f"{dir_path} is not a directory",
                {"Content-type": "text/plain"},
            )
        current_dir = os.path.abspath(self.file_serving_root)
        if not (
            dir_path_abs == current_dir or dir_path_abs.startswith(
                current_dir + os.sep)
        ):
            return self.response(
                403,
                "Forbidden",
                "Directory listing for parent directories is disabled.",
                {"Content-type": "text/plain"},
            )

        try:
            files = os.listdir(dir_path_abs)
            body = "\n".join(files)
            return self.response(200, "OK", body, {"Content-type": "text/plain"})
        except Exception as e:
            return self.response(
                404, "Not Found", str(e), {"Content-type": "text/plain"}
            )

    def http_upload(self, object_address, headers, body):
        # Extract filename from /upload/filename
        if object_address.startswith("/upload/"):
            filename = object_address[8:]  # Remove "/upload/" prefix
        else:
            filename = object_address.lstrip("/")

        if not filename:
            return self.response(
                400,
                "Bad Request",
                "No filename specified",
                {"Content-type": "text/plain"},
            )

        # Sanitize filename and create full path
        safe_filename = os.path.basename(filename)  # Remove any path traversal
        file_path = os.path.join(self.file_serving_root, safe_filename)

        try:
            with open(file_path, "wb+") as f:
                f.write(body)
                f.close()

            if self.logging:
                self.logging.info(
                    f"File uploaded: {safe_filename} ({len(body)} bytes)")

            return self.response(
                201,
                "Created",
                f"File {safe_filename} uploaded successfully ({len(body)} bytes)",
                {"Content-type": "text/plain"},
            )
        except Exception as e:
            if self.logging:
                self.logging.error(f"Upload error: {e}")
            return self.response(
                500,
                "Internal Server Error",
                f"Error uploading file: {str(e)}",
                {"Content-type": "text/plain"},
            )

    def http_delete(self, object_address, headers):
        # Extract filename from path like /delete/filename.txt
        if object_address.startswith("/delete/"):
            filename = object_address[8:]  # Remove "/delete/" prefix
        else:
            filename = object_address.lstrip("/")

        if not filename:
            return self.response(
                400,
                "Bad Request",
                "No filename specified",
                {"Content-type": "text/plain"},
            )

        file_path = os.path.join(self.file_serving_root, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return self.response(
                    200,
                    "OK",
                    f"File {filename} deleted successfully",
                    {"Content-type": "text/plain"},
                )
            else:
                return self.response(
                    404,
                    "Not Found",
                    f"File {filename} not found",
                    {"Content-type": "text/plain"},
                )
        except Exception as e:
            return self.response(
                500,
                "Internal Server Error",
                f"Error deleting file: {str(e)}",
                {"Content-type": "text/plain"},
            )


if __name__ == "__main__":
    httpserver = HttpServer()
    d = httpserver.proses("GET testing.txt HTTP/1.0")
    print(d)
    d = httpserver.proses("GET donalbebek.jpg HTTP/1.0")
    print(d)
