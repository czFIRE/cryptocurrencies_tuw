import json
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

    def receive_msg(self):
        """Function that waits for the next message, receives it, trys to decode it and returns it"""

        try:
            while True:
                msg = self.conn.recv(1024).decode(self.FORMAT)  # blocking. Receive 1024 bytes of message and decode it

                if msg == "b''" or msg == "\n" or msg == "\r" or len(msg) == 0:
                    continue

                utils.printer.printout("[RECEIVED]: " + msg)

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

        except ConnectionResetError:
            utils.printer.printout("Connection got killed!")
            return None
        except Exception as err:
            utils.printer.printout(f"Unexpected {err=}, {type(err)=}")
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
            "agent": os.getenv('NODE_NAME', default="Cool_Node")
        })

    def receive_hello(self, msg_json: dict) -> bool:
        if len(msg_json) > 3 or "type" not in msg_json or "version" not in msg_json:
            utils.printer.printout("[DISCONNECTING]: hello has wrong format")
            self.send_error("Hello has wrong format.")
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

    def receive_peers(self, msg_json: dict) -> bool:
        if len(msg_json) != 2 or "peers" not in msg_json or "type" not in msg_json:
            utils.printer.printout("[DISCONNECTING]: peers has wrong format")
            self.send_error("Peers has wrong format.")
            return False

        if msg_json["type"] != "peers":
            utils.printer.printout("[DISCONNECTING]: no peers sent")
            self.send_error("Sent no peers message after getpeers.")
            return False

        for peer in msg_json["peers"]:
            # Should probably do some RegEx here
            ipAndPort = peer.split(":")
            peerObj = Peer(ipAndPort[0], int(ipAndPort[1]))
            utils.peer_saver.add_peer(peerObj)

        utils.printer.printout("Succesfully added new peers!")
        return True

    def send_peers(self) -> bool:
        return self.send_message({
            "type": "peers",
            "peers": list(utils.peer_saver.peers.keys())
        })

    def send_error(self, error) -> bool:
        return self.send_message({
            "type": "error",
            "error ": error
        })

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

    def maintain_connection(self) -> None:
        """Loop trough new messages and answer them"""

        hello_received = False

        # Loop trough new received messages
        while True:
            msgs = self.receive_msg()

            # received something bad
            if (msgs is None):
                utils.printer.printout("Connection got closed, exiting!")
                return

            for i in msgs:
                if not i["type"]:
                    self.send_error("No valid message received")
                    return

                if i["type"] == "hello":
                    hello_received = self.receive_hello(i)

                if not hello_received:
                    self.send_error("Sent no hello message at start of conversation.")
                    return

                if i["type"] == "getpeers":
                    if (len(i) != 1):
                        utils.printer.printout("[DISCONNECTING]: getpeers has wrong format")
                        self.send_error("getpeers has wrong format.")
                        return
                    self.send_peers()

                if i["type"] == "peers":
                    self.receive_peers(i)
