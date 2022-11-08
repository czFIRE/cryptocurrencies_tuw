# Python file used for defining utilities
from sys import stdout
from typing import Iterable, TextIO
from datetime import date, datetime

import asyncio
from threading import Lock, Thread

import pickle
import os

from dotenv import load_dotenv

load_dotenv()
PRODUCTION = os.getenv('PRODUCTION', default=True) == 'True'

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

    def printout(self, msg, both: bool = True) -> None:
        if (PRODUCTION):
            return

        current_datetime = "[" + date.today().strftime("%d/%m/%Y") + " - " + datetime.now().strftime("%H:%M:%S") + "] "
        self.output_str.write(current_datetime + str(msg) + '\n')

        if (both and self.output_str != stdout):
            print(current_datetime + str(msg))


class PeerSaver:
    '''Used for saving and loading discovered peers'''

    peer_lock = Lock()
    peers: dict = {}

    # handle file overwriting in a nice way
    def __init__(self, file_location: str) -> None:
        self.file_location = file_location

        daemon = Thread(target=asyncio.run, args=(self.auto_save(3600),), daemon=True, name='Background')
        daemon.start()

        # Load all discovered peers
        self.load()

    def __del__(self) -> None:
        self.save()

    def load(self) -> None:
        if (not os.path.exists(self.file_location)):
            with open(self.file_location, 'wb') as file:
                self.save()
                return

        with open(self.file_location, 'rb') as file:
            self.peers = pickle.load(file)
            printer.printout("Loaded these peers: " + str(self.peers))

    def save(self) -> None:
        printer.printout("Saving peers!")
        with open(self.file_location, 'wb') as file:
            pickle.dump(self.peers, file)

    def add_peers(self, peer: Iterable) -> None:
        with self.peer_lock:
            self.peers.update(peer)

    async def auto_save(self, interval_sec):
        """Saves the work each hour"""

        await asyncio.sleep(30)
        self.save()

        # run forever
        while True:
            # block for the interval
            await asyncio.sleep(interval_sec)
            # perform the task
            self.save()


# Make a public instance of printer such that it is visible across the whole implementation
printer = Printer("log.txt")
peer_saver = PeerSaver("peer_db.pickle")