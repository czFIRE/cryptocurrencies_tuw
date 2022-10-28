import utils

from connection import Connection


class ServerConnection(Connection):

    def handle_client(self) -> None:
        utils.printer.printout(f"[NEW CONNECTION] {self.addr} connected.")

        # Send hello and get_peers
        if not self.send_hello():
            utils.printer.printout("Couldn't send the hello message!")
            return
        if not self.send_get_peers():
            utils.printer.printout("Couldn't send the get peers message!")
            return

        hello_received = False

        # Loop trough new received messages
        while True:
            msgs = self.receive_msg()

            for i in msgs:
                if not i["type"]:
                    self.send_error("No valid message received")

                if i["type"] == "hello":
                    hello_received = self.receive_hello(i)

                if not hello_received:
                    self.send_error("Sent no hello message at start of conversation.")
                    return

                if i["type"] == "getpeers":
                    self.send_peers()

                if i["type"] == "peers":
                    self.receive_peers()
