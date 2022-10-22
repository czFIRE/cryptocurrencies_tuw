import json
from socket import socket

import sys
import utils

class Connection:

    FORMAT = 'utf-8'

    def __init__(self, conn: socket, addr) -> None:
        self.addr = addr
        self.conn: socket = conn

    def __del__(self) -> None:
        # close the connection when out of scope or destroyed
        self.conn.close()

    
    def send_hello(self) -> bool:
        msg = json.dumps({  # Send the initial hello message
            "type": "hello",
            "version": "0.8.0",
            "agent": "Kool_node_1"
        })

        message = msg.encode(self.FORMAT)
        return (self.conn.send(message) == len(msg))

    def receive_hello(self) -> bool:
        keep_connection = True
        hello_sent = False

        while keep_connection:
            msg = self.conn.recv(1024).decode(self.FORMAT)  # blocking. Receive 1024 bytes of message and decode it
            self.conn.recv(1024)  # overread new line character

            if msg == "b''":
                continue

            utils.printer.printout("Received: " + msg)

            try:  # try decoding json message. Close connection if decoding error
                msg_json = json.loads(msg)
            except json.decoder.JSONDecodeError:
                utils.printer.printout("[DISCONNECTING]: no valid json received: '" + msg + "'")
                keep_connection = False
                continue

            if not hello_sent:
                if msg_json["type"] != "hello":
                    utils.printer.printout("[DISCONNECTING]: no hello sent")
                    keep_connection = False
                    break

                # add part that checks if the version isn't like 0.8.aaa or 0.8 => check it with their implementation what's valid here
                elif msg_json["version"][0:3] != "0.8":
                    utils.printer.printout("[DISCONNECTING]: Wrong version " + msg_json["version"][0:3])
                    keep_connection = False
                    break

                else:
                    utils.printer.printout("Hello sent")
                    hello_sent = True
                    #break

        return keep_connection

    def send_peers(self) -> bool:
        # TODO
        return False

    def receive_peers(self) -> bool:
        # TODO
        return False   

    def send_error(self) -> None:
        # TODO
        pass

    
    # Handle connection with one client
    def handle_client(self) -> None:
        #TODO - add try catch for error with "connection ended by remote host"

        utils.printer.printout(f"[NEW CONNECTION] {self.addr} connected.")

        if (not self.send_hello()):
            utils.printer.printout("Couldn't send the hello message!")
            return

        if (not self.receive_hello()):
            utils.printer.printout("Problem with getting hello")
            return

        if (not self.send_peers()):
            utils.printer.printout("Couldn't send the peers message!")
            return

        if (not self.receive_peers()):
            utils.printer.printout("Problem with getting peers")
            return

        # Add part to send error msg if connection failed
        #if (not keep_connection):
        #    pass
    