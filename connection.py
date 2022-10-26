import json
from socket import socket
import utils
import os


class Connection:
    FORMAT = 'utf-8'

    def __init__(self, conn: socket, addr) -> None:
        self.addr = addr
        self.conn: socket = conn

    def __del__(self) -> None:
        # close the connection when out of scope or destroyed
        utils.printer.printout("Closing connection")
        self.conn.close()

    # Function that waits for the next message, receives it, trys to decode it and returns it
    def receive_msg(self):
        while True:
            msg = self.conn.recv(1024).decode(self.FORMAT)  # blocking. Receive 1024 bytes of message and decode it
            self.conn.recv(1024)  # overread new line character

            if msg == "b''":
                continue

            utils.printer.printout("Received: " + msg)

            try:  # try decoding json message. Close connection if decoding error
                msg_json = json.loads(msg)
                return True, msg_json
            except json.decoder.JSONDecodeError:
                utils.printer.printout("No valid json received: '" + msg + "'")
                self.send_error("No valid json received.")
                return False, msg

    # Function that takes a json object and sends it to the client
    def send_message(self, msg_json) -> bool:
        msg = json.dumps(msg_json) + "\n"
        message = msg.encode(self.FORMAT)
        return self.conn.send(message) == len(msg)

    def send_hello(self) -> bool:
        return self.send_message({  # Send the initial hello message
            "type": "hello",
            "version": "0.8.0",
            "agent": os.getenv('NODE_NAME')
        })

    def receive_hello(self) -> bool:
        success, msg_json = self.receive_msg()

        if not success:
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

    def receive_peers(self) -> bool:
        # TODO
        return False

    def send_peers(self) -> bool:
        # TODO: read peers from file
        return self.send_message({
            "type": "peers",
            "peers": []
        })

    def send_error(self, error) -> bool:
        return self.send_message({
            "type": "error",
            "error ": error
        })

    def handle_client(self) -> None:
        # TODO - add try catch for error with "connection ended by remote host" - why would we need this? -flo

        utils.printer.printout(f"[NEW CONNECTION] {self.addr} connected.")

        # Send and receive hello, send get peers
        if not self.send_hello():
            utils.printer.printout("Couldn't send the hello message!")
            return
        if not self.receive_hello():
            utils.printer.printout("Problem with getting hello")
            return
        if not self.send_get_peers():
            utils.printer.printout("Couldn't send the get peers message!")
            return

        # Loop trough new received messages
        while True:
            success, msg_json = self.receive_msg()

            if not success:
                continue

            if not msg_json["type"]:
                self.send_error("No valid message received")

            if msg_json["type"] == "getpeers":
                self.send_peers()

            if msg_json["type"] == "peers":
                self.receive_peers()
