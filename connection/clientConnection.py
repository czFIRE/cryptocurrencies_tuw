import socket
import utils

from connection.connection import Connection


# Client to execute the peer discovery at node startup

class ClientConnection(Connection):

    def __init__(self, host: str, port: int, addr) -> None:
        self.host = host
        self.port = port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port)),
        super().__init__(s, addr)

    async def start_client(self) -> None:
        utils.printer.printout(f"[NEW OUTGOING CONNECTION] connecting to {self.host}:{self.port}")

        self.send_initial_messages()
        await self.maintain_connection()
