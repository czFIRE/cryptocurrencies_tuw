import asyncio
import ipaddress
import json
import re
from socket import socket
import os
import time

import sys

# setting path
import sys
import os

# Hack to make it import stuff from parent directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import utils
from peers import Peer


class Connection:
    FORMAT = 'utf-8'

    def __init__(self, conn: socket, addr) -> None:
        self.addr = addr
        self.conn: socket = conn

    def __del__(self) -> None:
        """ close the connection when out of scope or destroyed """
        utils.printer.printout("Closing connection")
        self.conn.close()

    async def receive_msg(self):
        """Function that waits for the next message, receives it, trys to decode it and returns it"""

        # solve loop closing
        loop = asyncio.get_event_loop()

        try:
            while True:
                #msg = self.conn.recv(1024).decode(self.FORMAT)  # blocking. Receive 1024 bytes of message and decode it
                msg = (await loop.sock_recv(self.conn, 1024)).decode(self.FORMAT)  # blocking. Receive 1024 bytes of message and decode it

                if msg == "b''" or msg == "\n" or msg == "\r" or len(msg) == 0:
                    await asyncio.sleep(1)
                    continue

                utils.printer.printout("[RECEIVED]: " + msg)

                # If the message doesn't end with a newline character, wait for the rest of the message
                if msg[-1] != "\n":
                    utils.printer.printout("No newline at end of message. Waiting for the rest of the message")
                    
                    #asyncio.wait_for()
                    
                    start = time.time()
                    while time.time() - 30 < start and msg[-1] != "\n":  # wait at most 30 seconds
                        msg += self.conn.recv(1024).decode(self.FORMAT)
                        utils.printer.printout("[RECEIVED] Msg extended to: " + msg)

                incoming_msg_que = []
                for substr in msg.split("\n"):
                    if substr == "b''" or substr == "\r" or len(substr) == 0 or substr == "\n":
                        continue

                    try:  # try decoding json message
                        incoming_msg_que.append(json.loads(substr))
                    except json.decoder.JSONDecodeError:
                        utils.printer.printout("No valid json received: '" + substr + "'")
                        self.send_error("No valid json received.")
                        return None

                return incoming_msg_que

        except ConnectionResetError:
            utils.printer.printout("Connection got killed!")
            return None
        except Exception as err:
            utils.printer.printout(f"Unexpected {err=}, {type(err)=}")
            print(f"Unexpected {err=}, {type(err)=}")
            return None

    def send_message(self, msg_json) -> bool:
        """ Function that takes a json object and sends it to the client"""

        msg = json.dumps(msg_json) + "\n"
        message = msg.encode(self.FORMAT)
        utils.printer.printout("[SENT] " + msg)
        return self.conn.send(message) == len(msg)

    def send_hello(self) -> bool:
        return self.send_message({  # Send the initial hello message
            "type": "hello",
            "version": "0.8.0",
            "agent": os.getenv('NODE_NAME', default="Fun_node_name")
        })

    def receive_hello(self, msg_json: dict) -> bool:
        if not self.check_msg_format(msg_json, 3, ["type", "version", "agent"], "hello has wrong format"):
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

    def receive_peers(self, msg_json) -> bool:
        if not self.check_msg_format(msg_json, 2, ["peers"], "peers has wrong format"):
            return False

        new_peers = []

        for peer in msg_json["peers"]:
            # Valid IP check
            peer_ip_port = peer.split(":")
            not_valid = ["127.0.0.0", "1.1.1.1", "8.8.8.8"]
            if len(peer_ip_port) > 1 and peer_ip_port[0] not in not_valid and str(peer_ip_port[-1]).isdigit():
                try:
                    ipaddress.ip_address(peer_ip_port[0])
                    peer_obj = Peer(peer_ip_port[0], peer_ip_port[1])
                    new_peers.append((peer.strip(), peer_obj))
                except ValueError:
                    # Accept anything with a "."
                    if "." in peer_ip_port[0]:
                        peer_obj = Peer(peer_ip_port[0], peer_ip_port[1])
                        new_peers.append((peer.strip(), peer_obj))
                    else:
                        utils.printer.printout("Not a valid IP: ", peer_ip_port[0])
            else:
                utils.printer.printout("Not a valid IP or port: ", peer)

        utils.peer_saver.add_peers(new_peers)
        utils.printer.printout("Succesfully added new peers!")
        return True

    def send_peers(self, msg) -> bool:
        if not self.check_msg_format(msg, 1, [], "getpeers has wrong format"):
            return False

        return self.send_message({
            "type": "peers",
            "peers": list(utils.peer_saver.peers.keys())
        })

    def send_error(self, error) -> bool:
        return self.send_message({
            "type": "error",
            "error ": error
        })

    def check_msg_format(self, msg, size, keys, error_msg) -> bool:
        """Check if a received message has the correct size and keys present. If not, send an error message"""

        if len(msg) != size or not all(item in msg for item in keys):
            utils.printer.printout(f"[WRONG FORMAT] {error_msg}")
            self.send_error(error_msg)
            return False

        return True

    def send_initial_messages(self) -> bool:
        """Send the messages needed at the start of a connection"""

        # Send hello and get_peers
        if not self.send_hello():
            utils.printer.printout("Couldn't send the hello message!")
            return False
        if not self.send_get_peers():
            utils.printer.printout("Couldn't send the get peers message!")
            return False
        return True

    def send_object(self, msg) -> bool:
        """Triggered by 'getobject'. Send back the requested object if we have it in db"""

        if not self.check_msg_format(msg, 2, ["objectid"], "getobject has wrong format"):
            return False

        # TODO: send the object
        return True


    def process_i_have_object(self, msg) -> bool:
        """Triggered by 'ihaveobject'. Check if we already have this object and if not, request it"""

        if not self.check_msg_format(msg, 2, ["objectid"], "ihaveobject has wrong format"):
            return False

        # TODO: check if object is in storage, request it otherwise
        return True


    def receive_object(self, msg) -> bool:
        """Triggered by 'object'.
            - Receive and store a new object, if it isn't already present in our db.
            - Gossip it to other peers"""

        if not self.check_msg_format(msg, 2, ["object"], "message of type 'object' has wrong format"):
            return False

        # TODO: Check if object is in storage, store and gossip it otherwise


    async def maintain_connection(self) -> None:
        """Loop trough new messages and answer them"""

        hello_received = False
        valid_types = ["hello", "getpeers", "peers", "getobject", "ihaveobject", "object"]

        # Loop trough new received messages
        while True:
            msgs = await self.receive_msg()

            # received something bad
            if msgs is None:
                utils.printer.printout("Connection got closed, exiting!")
                return

            for msg in msgs:
                print(msg)
                if "type" not in msg:
                    self.send_error("No valid message received")
                    return

                if msg["type"] == "hello":
                    hello_received = self.receive_hello(msg)

                if not hello_received:
                    self.send_error("Sent no hello message at start of conversation.")
                    return

                if msg["type"] == "getpeers":
                    if not self.send_peers(msg):
                        return

                if msg["type"] == "peers":
                    if not self.receive_peers(msg):
                        return

                if msg["type"] == "getobject":
                    if not self.send_object(msg):
                        return

                if msg["type"] == "object":
                    if not self.receive_object(msg):
                        return

                if msg["type"] == "ihaveobject":
                    if not self.process_i_have_object(msg):
                        return

                if msg["type"] not in valid_types:
                    # We should handle this somehow
                    utils.printer.printout("Unknown type: " + msg["type"])
                    continue
