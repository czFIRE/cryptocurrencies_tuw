# Python file used for defining utilities
from sys import stdout
from typing import Dict, TextIO
from datetime import date, datetime

import json
import os.path


# can be replaced by default logging from Python
class Printer:
    '''Class used for printing stuff either to a console or to a log file'''
    output_str: TextIO = stdout

    def __init__(self, output="") -> None:
        if output != "":
            try:
                self.output_str = open(output, mode='at')
            except:
                print("Can't open file for logging!")
                exit(1)

    def __del__(self) -> None:
        if (self.output_str != stdout):
            self.output_str.close()
        print("printer got destroyed")

    def printout(self, msg, both: bool = False) -> None:
        current_datetime = "[" + date.today().strftime("%d/%m/%Y") + " - " + datetime.now().strftime("%H:%M:%S") + "] "
        self.output_str.write(current_datetime + str(msg) + '\n')

        if (both and self.output_str != stdout):
            print(current_datetime + str(msg))


class PeerSaver:
    '''Used for saving and loading discovered peers'''

    # handle file overwriting in a nice way
    def __init__(self, file_location: str) -> None:
        self.peers: Dict = {}
        self.file_location = file_location

    def load(self) -> None:
        if (not os.path.exists(self.file_location)):
            with open(self.file_location, 'w') as file:
                return

        with open(self.file_location, 'r') as file:
            self.peers = json.loads(file.read())
            print(self.peers)

    def save(self) -> None:
        with open(self.file_location, 'w') as file:
            file.write(json.dumps(self.peers))

    def add_peer(self, peer) -> None:
        self.peers[peer.ip] = peer


# Make a public instance of printer such that it is visible across the whole implementation
printer = Printer()
peer_saver = PeerSaver("peer_db.json")
