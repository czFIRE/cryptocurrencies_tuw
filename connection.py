import json
from socket import socket
import utils
import os
import time


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

            utils.printer.printout("[RECEIVED]: " + msg)

            if msg == "b''" or msg == "\n" or msg == "\r" or len(msg) == 0:
                continue

            # If the message doesn't end with a newline character, wait for the rest of the message
            if msg[-1] != "\n":
                utils.printer.printout("No newline at end of message. Waiting for the rest of the message")
                start = time.time()
                while time.time() - 30 < start and msg[-1] != "\n":  # wait at most 30 seconds
                    msg += self.conn.recv(1024).decode(self.FORMAT)
                    utils.printer.printout("[RECEIVED] Msg extended to: " + msg)

            incoming_msg_que = []
            for i in msg.split("\n"):
                if i == "b''" or i == "\r" or len(i) == 0 or i == "\n":
                    continue

                try:  # try decoding json message
                    incoming_msg_que.append(json.loads(i))
                except json.decoder.JSONDecodeError:
                    utils.printer.printout("No valid json received: '" + i + "'")
                    self.send_error("No valid json received.")

            return incoming_msg_que

    # Function that takes a json object and sends it to the client
    def send_message(self, msg_json) -> bool:
        msg = json.dumps(msg_json) + "\n"
        message = msg.encode(self.FORMAT)
        utils.printer.printout("[SENT] " + msg)
        return self.conn.send(message) == len(msg)

    def send_hello(self) -> bool:
        return self.send_message({  # Send the initial hello message
            "type": "hello",
            "version": "0.8.0",
            "agent": os.getenv('NODE_NAME', default="Cool_Node")
        })

    def receive_hello(self, msg_json) -> bool:
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
