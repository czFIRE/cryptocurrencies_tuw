import socket
import json
import os
import time

from dotenv import load_dotenv

# A client for testing our functionality, not used in Production

HOST = socket.gethostbyname('localhost')  # The server's hostname or IP address
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

    json_transaction = json.dumps({
        "type": "object",
        "object": {
            "type":"transaction", 
            "inputs":[{
                "outpoint": {
                    "txid": "f71408bf847d7dd15824574a7cd4afdfaaa2866286910675cd3fc371507aa196" ,
                    "index": 0 
                    },
                "sig":"3869a9ea9e7ed926a7c8b30fb71f6ed151a132b03fd5dae764f015c98271000e7da322dbcfc97af7931c23c0fae060e102446ccff0f54ec00f9978f3a69a6f0f"
                }],
            "outputs": [{
                "pubkey": "077a2683d776a71139fd4db4d00c16703ba0753fc8bdc4bd6fc56614e659cde3" ,
                "value": 5100000000 
                }] 
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

    byte2 = json_transaction.encode('utf-8')
    print("Send: " + json_transaction)
    s.send(byte2)

    while True:
        data = s.recv(1024)
        print(f"Received: {data!r}")
