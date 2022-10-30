import socket
import json
import os
import time

from dotenv import load_dotenv

# A client for testing our functionality, not used in Production

HOST = "localhost"  # The server's hostname or IP address
load_dotenv()
PORT = int(os.getenv('PORT', default=18018))  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    json_message = json.dumps({  # Send the initial hello message
        "type": "hello",
        "version": "0.8.0",
        "agent": "Kerma-Core Server 0.8 _1"
    }) + "\n"

    json_getPeers = json.dumps({
        "type": "getpeers",
    }) + "\n"

    s.connect((HOST, PORT))

    part1 = json_message[0:15]
    part2 = json_message[15:]

    # split the message in two parts sent with 0.5 seconds time difference
    byt = part1.encode('utf-8')
    print("Sent: " + str(byt))
    s.send(byt)
    time.sleep(0.5)
    byt = part2.encode('utf-8')
    print("Sent: " + str(byt))
    s.send(byt)

    data = s.recv(1024)

    print(f"Received: {data!r}")

    byt = json_getPeers.encode('utf-8')
    print("Sent: " + json_getPeers)
    s.send(byt)

    while True:
        data = s.recv(1024)
        print(f"Received: {data!r}")
