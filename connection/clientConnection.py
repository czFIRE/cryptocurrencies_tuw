import socket

from connection.connection import Connection


# Client to execute the peer discovery at node startup

class ClientConnection(Connection):

    def __init__(self, host, port, addr) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port)),
        super().__init__(s, addr)

    def start_client(self) -> None:
        self.send_initial_messages()
        self.maintain_connection()
