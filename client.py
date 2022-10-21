import socket
import json

import utils

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 18018  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    json_message = json.dumps({  # Send the initial hello message
        "type": "hello",
        "version": "0.8.0",
        "agent": "Kerma-Core Server 0.8 _1"
    })

    json_getPeers = json.dumps({
        "type": "getpeers",
        "version": "0.8.0",
        "agent": "Kerma-Core Server 0.8 _2"
    })

    s.connect((HOST, PORT))

    byt = json_message.encode('utf-8')
    utils.printer.printout("Sent: " + json_message)
    s.send(byt)
    data = s.recv(1024)

    utils.printer.printout(f"Received {data!r}")

    byt = json_getPeers.encode('utf-8')
    utils.printer.printout("Sent: " + json_getPeers)
    s.send(byt)
    data = s.recv(1024)

utils.printer.printout(f"Received {data!r}")
