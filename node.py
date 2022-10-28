import socket
import threading
import os
from dotenv import load_dotenv
from serverConnection import ServerConnection
import utils


class Node:
    load_dotenv()
    PORT = int(os.getenv('PORT', default=18018))
    SERVER = socket.gethostbyname('localhost')  # socket.gethostname()
    ADDR = (SERVER, PORT)

    # thread_arr = []

    def __init__(self) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDR)
        utils.printer.printout("Server at " + self.SERVER + " Port " + str(self.PORT))

    def __del__(self) -> None:
        self.server.close()

    def start(self) -> None:
        self.server.listen()  # Listen to new connections
        while True:
            conn, addr = self.server.accept()  # blocking
            thread = threading.Thread(target=self.handle_connection, args=(conn, addr))  # run function in new thread !!!!!! don't forget to close threads on exit -> add to __del__ of node class
            # self.thread_arr.append(thread)
            thread.start()
            utils.printer.printout(
                f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")  # Main thread is always running, therefore substract 1

    def handle_connection(self, conn, addr) -> None:
        connectio = ServerConnection(conn, addr)
        connectio.handle_client()

    def peer_discovery(self, conn, addr) -> None:
        pass


# Reimplement this as such that this is a class that we run on startup
# for each client startup connection that handles everything accompanied by it
# remove global variables and have them as a part of the node class

if __name__ == "__main__":
    utils.printer.printout("[STARTING] server is starting...")
    node = Node()
    node.start()
