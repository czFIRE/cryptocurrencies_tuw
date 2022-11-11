import socket
import json
import os
import time

from dotenv import load_dotenv

# A client for testing our functionality, not used in Production

HOST = socket.gethostname()  # The server's hostname or IP address
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

    json_object = json.dumps({
        "type": "object",
        "object": {
            "type": "block",
            "txids": ["740bcfb434c89abe57bb2bc80290cd5495e87ebf8cd0dadb076bc50453590104"],
            "nonce": "a26d92800cf58e88a5ecf37156c031a4147c2128beeaf1cca2785c93242a4c8b",
            "previd": "0024839ec9632d382486ba7aac7e0bda3b4bda1d4bd79be9ae78e7e1e813ddd8",
            "created": "1622825642",
            "T": "003a000000000000000000000000000000000000000000000000000000000000"
        }
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

    byte = json_object.encode('utf-8')
    print("Send: " + json_object)
    s.send(byte)

    while True:
        data = s.recv(1024)
        print(f"Received: {data!r}")
