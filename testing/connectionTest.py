import json
from socket import socket
import time
import os

import sys
sys.path.append('../cryptocurrencies_tuw')

class ConnectionTest:
    FORMAT = 'utf-8'

    def __init__(self, conn: socket, addr) -> None:
        self.addr = addr
        self.conn: socket = conn

    def __del__(self) -> None:
        # close the connection when out of scope or destroyed
        print("Closing connection")
        self.conn.close()

    # Function that waits for the next message, receives it, trys to decode it and returns it
    def receive_msg(self):
        while True:
            time.sleep(0.25)
            msg = self.conn.recv(2048).decode(self.FORMAT)  # blocking. Receive 1024 bytes of message and decode it

            if msg == "b''" or msg == "\n" or msg == "\r" or len(msg) == 0:
                continue

            incoming_msg_que = []
            for i in msg.split("\n"):
                if i == "b''" or i == "\r" or len(i) == 0 or i == "\n":
                    continue

                print("[RECEIVED]: " + i)

                try:  # try decoding json message
                    incoming_msg_que.append(json.loads(i))
                except json.decoder.JSONDecodeError:
                    print("No valid json received: '" + i + "'")
                    self.send_error("No valid json received.")

            return incoming_msg_que

    # Function that takes a json object and sends it to the client
    def send_message(self, msg_json) -> bool:
        msg = json.dumps(msg_json) + "\n"
        message = msg.encode(self.FORMAT)
        print("[SENT] " + msg)
        return self.conn.send(message) == len(msg)
    
    def send_message_in_parts(self, msg_json) -> bool:
        msg_length = len(msg_json)
        split = msg_length//2-1
        msg_1 = json.dumps(msg_json[0:split])
        msg_2 = json.dumps(msg_json[split::]) + "\n"
        message_1 = msg_1.encode(self.FORMAT)
        message_2 = msg_2.encode(self.FORMAT)
        print("[SENT] " + msg_1)
        self.conn.send(message_1)
        print("[SENT] " + msg_2)
        self.conn.send(message_2)

        return True

    def send_hello(self) -> bool:
        return self.send_message({  # Send the initial hello message
            "type": "hello",
            "version": "0.8.0",
            "agent": os.getenv('NODE_NAME', default="Cool_Node")
        })

    def receive_hello(self, msg_json) -> bool:
        if msg_json["type"] != "hello":
            print("[DISCONNECTING]: no hello sent")
            self.send_error("Sent no hello message at start of conversation.")
            return False

        # If the version you receive differs from 0.8.x you must disconnect.
        elif msg_json["version"][0:3] != "0.8" or len(msg_json["version"]) < 5:
            print("[DISCONNECTING]: Wrong version " + msg_json["version"][0:3])
            self.send_error("Wrong protocol version")
            return False

        else:
            print("Hello received")
            return True

    def send_get_peers(self) -> bool:
        return self.send_message({
            "type": "getpeers"
        })

    def receive_peers(self, peerList) -> bool:
        for i in peerList:
            print(i)
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

        print(f"[NEW CONNECTION] {self.addr} connected.")

        # Send hello and get_peers
        if not self.send_hello():
            print("Couldn't send the hello message!")
            return
        if not self.send_get_peers():
            print("Couldn't send the get peers message!")
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

                    # Send split message with 0.1 sec between
                    msg_1 = '{"type": "ge'
                    msg_2 = 'tpeers"}' + "\n"
                    message_1 = msg_1.encode(self.FORMAT)
                    message_2 = msg_2.encode(self.FORMAT)
                    print("[SENT] " + msg_1)
                    print("[SENT] " + msg_2)
                    self.conn.send(message_1)
                    time.sleep(0.1)
                    self.conn.send(message_2)

                if i["type"] == "peers":
                    if i["peers"]:
                        self.receive_peers(i["peers"])
