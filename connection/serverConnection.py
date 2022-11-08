import utils

from connection.connection import Connection


# Server to handle incoming connections

class ServerConnection(Connection):

    async def handle_client(self) -> None:
        utils.printer.printout(f"[NEW INCOMING CONNECTION] {self.addr} connected.")

        self.send_initial_messages()
        await self.maintain_connection()


