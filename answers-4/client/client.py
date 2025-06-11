import socket
import os
import ssl
import logging
import json
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class HTTPClient:
    def __init__(self):
        self.session_cookies = {}

    def make_socket(self, destination_address="localhost", port=80):
        """Create a regular socket connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (destination_address, port)
            logging.info(f"Connecting to {server_address}")
            sock.connect(server_address)
            return sock
        except Exception as e:
            logging.error(f"Socket creation error: {str(e)}")
            return None

    def make_secure_socket(
        self, destination_address="localhost", port=443, verify_certs=False
    ):
        """Create a secure SSL/TLS socket connection"""
        try:
            context = ssl.create_default_context()

            if verify_certs:
                # Enable certificate verification
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                logging.info("SSL certificate verification enabled")
            else:
                # Disable certificate verification (for testing)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                logging.warning(
                    "SSL certificate verification disabled - for testing only"
                )

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (destination_address, port)
            logging.info(f"Connecting securely to {server_address}")
            sock.connect(server_address)

            secure_socket = context.wrap_socket(
                sock, server_hostname=destination_address
            )

            # Log certificate information if verification is enabled
            if verify_certs:
                cert = secure_socket.getpeercert()
                if cert:
                    logging.info(f"Certificate verified for {destination_address}")
                    logging.info(
                        f"Certificate subject: {cert.get('subject', 'Unknown')}"
                    )
                    logging.info(f"Certificate issuer: {cert.get('issuer', 'Unknown')}")
                else:
                    logging.warning("No certificate information available")

            return secure_socket
        except ssl.SSLError as e:
            logging.error(f"SSL certificate verification failed: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Secure socket creation error: {str(e)}")
            return None

    def send_request(self, host, port, request, is_secure=False, verify_certs=False):
        """Send HTTP request and receive response"""
        if is_secure:
            sock = self.make_secure_socket(host, port, verify_certs)
        else:
            sock = self.make_socket(host, port)

        if not sock:
            return None

        request = request + "\r\n\r\n".encode()
        try:
            sock.sendall(request)
            logging.info("HTTP request sent")

            # Receive response
            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data

                if len(response) > 0 and response.endswith(b"\r\n\r\n"):
                    break

            sock.close()
            return response

        except Exception as e:
            logging.error(f"Request sending error: {str(e)}")
            return None

    def get_request(self, url, headers=None, verify_certs=False):
        """Perform GET request"""
        parsed = urlparse(url)
        host = parsed.netloc
        path = parsed.path if parsed.path else "/"
        port = 443 if parsed.scheme == "https" else 80
        is_secure = parsed.scheme == "https"

        request_headers = {
            "Host": host,
            "User-Agent": "Python-HTTPClient/1.0",
            "Accept": "*/*",
            "Connection": "close",
        }

        if headers:
            request_headers.update(headers)

        request = f"GET {path} HTTP/1.1\r\n"
        logging.info(request)
        for key, value in request_headers.items():
            request += f"{key}: {value}\r\n"
        request += "\r\n"
        request = request.encode("utf-8")

        logging.info(f"GET request to {url}")
        response = self.send_request(host, port, request, is_secure, verify_certs)

        self._save_response_to_file(response, path)

        return response.decode("utf-8", errors="ignore")

    def _save_response_to_file(self, response, path):
        """Save HTTP response to file, separating headers from body"""
        if path.endswith("/") or path.endswith("."):
            return
        filename = os.path.basename(path)
        print(filename)
        try:
            # Split headers and body
            if b"\r\n\r\n" in response:
                headers, body = response.split(b"\r\n\r\n", 1)
            else:
                headers = response
                body = b""

            # Save body to file
            with open(filename, "wb") as f:
                f.write(body)

            logging.info(f"File saved as: {filename}")
            logging.info(f"File size: {len(body)} bytes")

            # Return headers as string for display
            return

        except Exception as e:
            logging.error(f"Error saving file {filename}: {e}")
            return

    def delete_request(self, url, headers=None, verify_certs=False):
        """Perform DELETE request"""
        parsed = urlparse(url)
        host = parsed.netloc
        path = parsed.path if parsed.path else "/"
        port = 443 if parsed.scheme == "https" else 80
        is_secure = parsed.scheme == "https"

        request_headers = {
            "Host": host,
            "User-Agent": "Python-HTTPClient/1.0",
            "Accept": "*/*",
            "Connection": "close",
        }

        if headers:
            request_headers.update(headers)

        request = f"DELETE {path} HTTP/1.1\r\n"
        logging.info(request)
        for key, value in request_headers.items():
            request += f"{key}: {value}\r\n"
        request += "\r\n"
        request = request.encode("utf-8")

        logging.info(f"DELETE request to {url}")
        return self.send_request(host, port, request, is_secure, verify_certs).decode(
            "utf-8", errors="ignore"
        )

    def post_request(self, url, data=None, headers=None, verify_certs=False):
        """Perform POST request"""
        parsed = urlparse(url)
        host = parsed.netloc
        path = parsed.path if parsed.path else "/"
        port = 443 if parsed.scheme == "https" else 80
        is_secure = parsed.scheme == "https"

        if data is None:
            data = ""
        if isinstance(data, dict):
            data = json.dumps(data)

        request_headers = {
            "Host": host,
            "User-Agent": "Python-HTTPClient/1.0",
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Content-Length": str(len(data)),
            "Connection": "close",
        }

        if headers:
            request_headers.update(headers)

        request = f"POST {path} HTTP/1.1\r\n"
        logging.info(request)
        for key, value in request_headers.items():
            request += f"{key}: {value}\r\n"
        request = request.encode()
        request += "\r\n".encode()
        if type(data) is not bytes:
            data = data.encode()

        request += data

        logging.info(f"POST request to {url}")
        return self.send_request(host, port, request, is_secure, verify_certs).decode(
            "utf-8", errors="ignore"
        )


if __name__ == "__main__":
    address = "http://172.16.16.101"
    client = HTTPClient()
    print("--------------Azarel's HTTP Client 1.0--------------")
    print("Input format: <request> <param>")
    print("Available commands:")
    print("  get <path> - GET request")
    print("  post <path> <data> - POST request with data")
    print("  upload <filename> <data> - Upload file with data")
    print("  delete <filename> - DELETE request")
    print("  exit - Quit the client")
    print()
    while True:
        prompt = input("> ")
        request, param = prompt.split(" ", 1) if " " in prompt else (prompt, "")
        if request.lower() == "exit":
            response = None
            break
        elif request.lower() == "get":
            cleaned_param = param.lstrip("/")
            target_url = f"{address.rstrip('/')}/{cleaned_param}"

            response = client.get_request(target_url, {}, verify_certs=False)
        elif request.lower() == "delete":
            cleaned_param = param.lstrip("/")
            target_url = f"{address.rstrip('/')}/delete/{cleaned_param}"

            response = client.delete_request(target_url, {}, verify_certs=False)
        elif request.lower() == "post":
            # Parse POST command: post <path> <data>
            parts = param.split(" ", 1) if " " in param else [param, ""]
            post_path = parts[0].lstrip("/")
            post_data = parts[1] if len(parts) > 1 else ""

            target_url = f"{address.rstrip('/')}/{post_path}"

            response = client.post_request(
                target_url, post_data, {}, verify_certs=False
            )

        elif request.lower() == "upload":
            # Parse UPLOAD command: upload <filename> <data>
            if " " not in param:
                try:
                    with open(param, "rb") as f:
                        file_data = f.read()
                        f.close()

                    filename = param
                except FileNotFoundError:
                    logging.error(f"File {param} not found")
                    continue
                except Exception as e:
                    logging.error(f"Error reading file {param}: {e}")
                    continue
            else:
                parts = param.split(" ", 1)
                filename = parts[0]
                file_data = parts[1]

            target_url = f"{address.rstrip('/')}/upload/{filename}"

            response = client.post_request(
                target_url,
                file_data,
                {"Content-Type": "text/plain"},
                verify_certs=False,
            )

        if response:
            lines = response.split("\n")
            for i, line in enumerate(lines[:30]):
                logging.info(line)
            if len(lines) > 30:
                logging.info(
                    f"... (the rest {len(lines) - 30} lines response truncated, total lines: {len(lines)})"
                )
        else:
            logging.warning("Response is empty or an error occurred.")
