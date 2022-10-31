import socket
from connectionTest import ConnectionTest

HOST = "localhost"  # The server's hostname or IP address
PORT = 18018  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    connectio = ConnectionTest(s, HOST)
    connectio.handle_client()