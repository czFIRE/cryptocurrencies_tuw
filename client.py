import socket
import json
import os
import time

from dotenv import load_dotenv

import utils

# Client to execute the peer discovery at node startup

HOST = "127.0.0.1"  # The server's hostname or IP address
load_dotenv()
PORT = int(os.getenv('PORT'))  # The port used by the server


class Client:

    def __init__(self, host, port) -> None:
        self.host = host
        self.port = port

msg_hello = json.dumps({
    "type": "hello",
    "version": "0.8.0",
    "agent": "Kerma-Core Server 0.8 _1"
}) + "\n"

msg_getpeers = json.dumps({
    "type": "getpeers",
    "version": "0.8.0",
    "agent": "Kerma-Core Server 0.8 _2"
}) + "\n"

s.connect((HOST, PORT))

part1 = json_message[0:15]
part2 = json_message[15:]

# split the message in two parts sent with 0.5 seconds time difference
byt = part1.encode('utf-8')
utils.printer.printout("Sent: " + str(byt))
s.send(byt)
time.sleep(0.5)
byt = part2.encode('utf-8')
utils.printer.printout("Sent: " + str(byt))
s.send(byt)

data = s.recv(1024)

utils.printer.printout(f"Received: {data!r}")

byt = json_getPeers.encode('utf-8')
utils.printer.printout("Sent: " + json_getPeers)
s.send(byt)

while True:
    data = s.recv(1024)
    utils.printer.printout(f"Received: {data!r}")
