import urllib.request
from sys import platform

from peers.Peer import Peer

from dotenv import load_dotenv
import os

load_dotenv()

HOST = "localhost" if platform in ["win32", "cygwin"] else "0.0.0.0"
PORT = int(os.getenv('PORT', default=18018))
VERSION = '0.8.0'
AGENT = os.getenv('NODE_NAME', default="Fun_node_name")

SERVICE_LOOP_DELAY = 10
LOW_CONNECTION_THRESHOLD = 3
HELLO_MSG_TIMEOUT = 10.0

BOOTSTRAP_NODE = Peer("128.130.122.101", 18018)
OBJECT_ID_GENESIS_BLOCK = "00000000a420b7cefa2b7730243316921ed59ffe836e111ca3801f82a4f5360e"

EXTERNAL_IP = urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')

BANNED_HOSTS = [
    "1.1.1.1",
    "8.8.8.8",
    "20.23.212.159",    # excessive ports, see TUWEL
    "84.115.238.131",   # excessive ports
    "85.127.44.22",     # excessive ports
]

PRELOADED_PEERS = [
    BOOTSTRAP_NODE,
]

TRANSACTIONS_ASKING_TIMEOUT = 5

BLOCK_TARGET = "00000002af000000000000000000000000000000000000000000000000000000"