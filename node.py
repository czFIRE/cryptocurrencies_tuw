import socket
import threading
import json

import utils

PORT = 18018
SERVER = socket.gethostbyname('localhost') #socket.gethostname()
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
utils.printer.printout("Server at " + SERVER + " Port " + str(PORT))


# Handle connection with one client
def handle_client(conn, addr):
    utils.printer.printout(f"[NEW CONNECTION] {addr} connected.")

    msg = json.dumps({  # Send the initial hello message
        "type": "hello",
        "version": "0.8.0",
        "agent": "Kerma-Core Server 0.8"
    })
    message = msg.encode(FORMAT)
    conn.send(message)

    connected = True
    hello_sent = False

    while connected:
        msg = conn.recv(1024).decode(FORMAT)  # blocking. Receive 1024 bytes of message and decode it
        conn.recv(1024)  # overread new line character

        if msg == "b''":
            continue

        utils.printer.printout("Received: " + msg)

        try:  # try decoding json message. Close connection if decoding error
            msg_json = json.loads(msg)
        except json.decoder.JSONDecodeError:
            utils.printer.printout("[DISCONNECTING]: no valid json received: '" + msg + "'")
            connected = False
            continue

        if not hello_sent:
            if msg_json["type"] != "hello":
                utils.printer.printout("[DISCONNECTING]: no hello sent")
                connected = False
            elif msg_json["version"][0:3] != "0.8":
                utils.printer.printout("[DISCONNECTING]: Wrong version " + msg_json["version"][0:3])
                connected = False
            else:
                utils.printer.printout("Hello sent")
                hello_sent = True

    conn.close()


def start():
    server.listen()  # Listen to new connections
    while True:
        conn, addr = server.accept()  # blocking
        thread = threading.Thread(target=handle_client, args=(conn, addr))  # run function in new thread
        thread.start()
        utils.printer.printout(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")  # Main thread is always running, therefore substract 1


utils.printer.printout("[STARTING] server ist starting...")
start()


