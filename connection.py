import json
from socket import socket
import utils


class Connection:
    FORMAT = 'utf-8'

    def __init__(self, conn: socket, addr) -> None:
        self.addr = addr
        self.conn: socket = conn

    def __del__(self) -> None:
        # close the connection when out of scope or destroyed
        utils.printer.printout("Closing connection")
        self.conn.close()

    def send_hello(self) -> bool:
        msg = json.dumps({  # Send the initial hello message
            "type": "hello",
            "version": "0.8.0",
            "agent": "Kool_node_1"
        })

        message = msg.encode(self.FORMAT)
        return self.conn.send(message) == len(msg)

    def receive_hello(self) -> bool:
        while True:
            msg = self.conn.recv(1024).decode(self.FORMAT)  # blocking. Receive 1024 bytes of message and decode it
            self.conn.recv(1024)  # overread new line character

            if msg == "b''":
                continue

            utils.printer.printout("Received: " + msg)

            try:  # try decoding json message. Close connection if decoding error
                msg_json = json.loads(msg)
            except json.decoder.JSONDecodeError:
                utils.printer.printout("[DISCONNECTING]: no valid json received: '" + msg + "'")
                self.send_error("No valid json received.")
                return False

            if msg_json["type"] != "hello":
                utils.printer.printout("[DISCONNECTING]: no hello sent")
                self.send_error("Sent no hello message at start of conversation.")
                return False

            # If the version you receive differs from 0.8.x you must disconnect.
            elif msg_json["version"][0:3] != "0.8" or len(msg_json["version"]) < 5:
                utils.printer.printout("[DISCONNECTING]: Wrong version " + msg_json["version"][0:3])
                self.send_error("Wrong protocol version")
                return False

            else:
                utils.printer.printout("Hello received")
                return True

    def send_get_peers(self) -> bool:
        return self.send_message({
            "type": "getpeers"
        })

    def send_peers(self) -> bool:
        # TODO: read peers from file
        return self.send_message({
            "type": "peers",
            "peers": []
        })

    def receive_peers(self) -> bool:
        # TODO
        return False

    def send_error(self, error) -> bool:
        return self.send_message({
            "type": "error",
            "error ": error
        })

    # Function that takes a json object and sends it to the client
    def send_message(self, msg_json) -> bool:
        msg = json.dumps(msg_json) + "\n"
        message = msg.encode(self.FORMAT)
        return self.conn.send(message) == len(msg)

    # Handle connection with one client
    def handle_client(self) -> None:
        # TODO - add try catch for error with "connection ended by remote host"

        utils.printer.printout(f"[NEW CONNECTION] {self.addr} connected.")

        if not self.send_hello():
            utils.printer.printout("Couldn't send the hello message!")
            return

        if not self.receive_hello():
            utils.printer.printout("Problem with getting hello")
            return

        if not self.send_get_peers():
            utils.printer.printout("Couldn't send the peers message!")
            return

        if not self.receive_peers():
            utils.printer.printout("Problem with getting peers")
            return

        # Add part to send error msg if connection failed
        # if (not keep_connection):
        #    pass
