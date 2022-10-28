import utils

from connection.connection import Connection


# Server to handle incoming connections

class ServerConnection(Connection):

    def handle_client(self) -> None:
        utils.printer.printout(f"[NEW CONNECTION] {self.addr} connected.")

        self.send_initial_messages()
        self.maintain_connection()


