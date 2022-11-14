import asyncio
import copy
import ipaddress
import json
from socket import socket
import time
import ed25519

import threading
import math

# setting path
import sys
import os

# Hack to make it import stuff from parent directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import utils
from peers import Peer
from txobject import TxObject, TransactionObject, CoinbaseTransaction
from hashlib import sha256

CURR_OBJ_HASH = ""

class Connection:
    FORMAT = 'utf-8'

    last_hash = ""
    curr_hash = "a"

    cv = threading.Condition()

    def __init__(self, conn: socket, addr) -> None:
        self.addr = addr
        self.conn: socket = conn
        threading.Thread(target=self.broadcast_object)

    def __del__(self) -> None:
        """ close the connection when out of scope or destroyed """
        utils.printer.printout("Closing connection")
        self.conn.close()

    def object_got(self, ob_hash: str):
        CURR_OBJ_HASH = ob_hash

        self.curr_hash = ob_hash
           # Gossip object to peers
        #self.gossip_object(ob_hash)

        self.cv.notify_all()

            # this is a hack I'm ashamed of
        time.sleep(0.15)

        CURR_OBJ_HASH = ""

    def broadcast_object(self):
        while True:
            self.cv.wait_for(lambda: self.last_hash != self.curr_hash)
            self.last_hash = self.curr_hash
            self.gossip_object(self.last_hash)

    async def receive_msg(self):
        """Function that waits for the next message, receives it, trys to decode it and returns it"""

        # solve loop closing
        loop = asyncio.get_event_loop()

        try:
            while True:
                # msg = self.conn.recv(1024).decode(self.FORMAT)  # blocking. Receive 1024 bytes of message and decode it
                msg = (await loop.sock_recv(self.conn, 1024)).decode(
                    self.FORMAT)  # blocking. Receive 1024 bytes of message and decode it

                if msg == "b''" or msg == "\n" or msg == "\r" or len(msg) == 0:
                    await asyncio.sleep(1)
                    continue

                utils.printer.printout("[RECEIVED]: " + msg)

                # If the message doesn't end with a newline character, wait for the rest of the message
                if msg[-1] != "\n":
                    utils.printer.printout("No newline at end of message. Waiting for the rest of the message")

                    # asyncio.wait_for()

                    start = time.time()
                    while time.time() - 30 < start and msg[-1] != "\n":  # wait at most 30 seconds
                        msg += (await loop.sock_recv(self.conn, 1024)).decode(self.FORMAT)
                        utils.printer.printout("[RECEIVED] Msg extended to: " + msg)

                incoming_msg_que = []
                for substr in msg.split("\n"):
                    if substr == "b''" or substr == "\r" or len(substr) == 0 or substr == "\n":
                        continue

                    try:  # try decoding json message
                        incoming_msg_que.append(json.loads(substr))
                    except json.decoder.JSONDecodeError:
                        utils.printer.printout("No valid json received: '" + substr + "'")
                        self.send_error("No valid json received.")
                        return None

                return incoming_msg_que

        except ConnectionResetError:
            utils.printer.printout("Connection got killed!")
            return "kill"
        except Exception as err:
            utils.printer.printout(f"Unexpected {err=}, {type(err)=}")
            print(f"Unexpected {err=}, {type(err)=}")
            return "kill"

    def send_message(self, msg_json) -> bool:
        """ Function that takes a json object and sends it to the client"""

        msg = json.dumps(msg_json) + "\n"
        message = msg.encode(self.FORMAT)
        utils.printer.printout("[SENT] " + msg)
        return self.conn.send(message) == len(msg)

    def send_hello(self) -> bool:
        return self.send_message({  # Send the initial hello message
            "type": "hello",
            "version": "0.8.0",
            "agent": os.getenv('NODE_NAME', default="Fun_node_name")
        })

    def receive_hello(self, msg_json: dict) -> bool:
        if not self.check_msg_format(msg_json, 3, ["type", "version", "agent"], "hello has wrong format"):
            return False

        # If the version you receive differs from 0.8.x you must disconnect.
        elif msg_json["version"][0:3] != "0.8" or len(msg_json["version"]) < 5:
            utils.printer.printout("[DISCONNECTING]: Wrong version " + msg_json["version"][0:3])
            self.send_error("Wrong protocol version")
            return False

        else:
            utils.printer.printout("Hello received")
            return True

    def send_get_peers(self) -> bool:
        return self.send_message({
            "type": "getpeers"
        })

    def receive_peers(self, msg_json) -> bool:
        if not self.check_msg_format(msg_json, 2, ["peers"], "peers has wrong format"):
            return False

        new_peers = []

        for peer in msg_json["peers"]:
            # Valid IP check
            peer_ip_port = peer.split(":")
            not_valid = ["127.0.0.0", "1.1.1.1", "8.8.8.8"]
            if len(peer_ip_port) > 1 and peer_ip_port[0] not in not_valid and str(peer_ip_port[-1]).isdigit():
                try:
                    ipaddress.ip_address(peer_ip_port[0])
                    peer_obj = Peer(peer_ip_port[0], peer_ip_port[1])
                    new_peers.append((peer.strip(), peer_obj))
                except ValueError:
                    # Accept anything with a "."
                    if "." in peer_ip_port[0]:
                        peer_obj = Peer(peer_ip_port[0], peer_ip_port[1])
                        new_peers.append((peer.strip(), peer_obj))
                    else:
                        utils.printer.printout("Not a valid IP: ", peer_ip_port[0])
            else:
                utils.printer.printout("Not a valid IP or port: ", peer)

        utils.peer_saver.add_peers(new_peers)
        utils.printer.printout("Succesfully added new peers!")
        return True

    def send_peers(self, msg) -> bool:
        if not self.check_msg_format(msg, 1, [], "getpeers has wrong format"):
            return False

        return self.send_message({
            "type": "peers",
            "peers": list(utils.peer_saver.peers.keys())
        })

    def send_error(self, error) -> bool:
        return self.send_message({
            "type": "error",
            "error ": error
        })

    def check_msg_format(self, msg, size, keys, error_msg) -> bool:
        """Check if a received message has the correct size and keys present. If not, send an error message"""

        if len(msg) != size or not all(item in msg for item in keys):
            utils.printer.printout(f"[WRONG FORMAT] {error_msg}")
            self.send_error(error_msg)
            return False

        return True
    
    def valid_transaction(self, ob) -> bool:
        """ Check if valid transaction. If not, send error message """
        # Could maybe move this functionality to utils?

        if not self.check_msg_format(ob, 3, ["type", "inputs", "outputs"], "message of type 'transaction' has wrong format"):
            return False
        
        # The message that is signed is the plaintext transaction with null as signature?
        signatures = []
        plaintext = copy.deepcopy(ob) 
        for inp in plaintext["inputs"]:
            inp["sig"] = None
        plaintext = str(plaintext)


        inputs = ob["inputs"]
        for input in inputs:
            if not self.check_msg_format(input, 2, ["outpoint", "sig"], "message of type 'transaction' has wrong format"):
                return False

            # Check outpoint. Valid txid in object database, index less than number of outputs in outpoint transaction
            outpoint = input["outpoint"]
            if not self.check_msg_format(outpoint, 2, ["txid", "index"], "message of type 'transaction' has wrong format"):
                return False
            
            txid = outpoint["txid"]
            prev_transaction = 0
            # Find the transaction the txid is pointing to
            if txid not in utils.object_saver.objects:
                return False
            
            # TODO replace it here with a hash
            prev_transaction = utils.object_saver.objects[txid]

            index = outpoint["index"]
            if index > len(prev_transaction.outputs) - 1:
                return False
 
            signatures.append(input["sig"])
        
        outputs = ob["outputs"]
        for output in outputs:
            if not self.check_msg_format(output, 2, ["pubkey", "value"], "message of type 'transaction' has wrong format"):
                return False
            
            if int(output["value"]) < 0:
                return False
            
            # b) For each input, verify the signature. Our protocol uses ed25519 signatures.
            i = outputs.index(output)
            pubkey = output["pubkey"]
            verifying_key = ed25519.VerifyingKey(pubkey, encoding="hex")
            try: 
                # uses pub key on the plaintext transaction message, with sign = null
                verifying_key.verify(signatures[i], plaintext, encoding='hex')
                print("The signature is valid.")
            except:
                print("Invalid signature")
                return False

        # TODO: d) Transactions must respect the law of conservation, i.e. the sum of all input values 
        # is at least the sum of output values

        # for tx in inputs:
        #   sum += tx.value

        # for value in outputs:
        #   out_sum += value

        #   return (sum >= outputs):

        return True

    def send_initial_messages(self) -> bool:
        """Send the messages needed at the start of a connection"""

        # Send hello and get_peers
        if not self.send_hello():
            utils.printer.printout("Couldn't send the hello message!")
            return False
        if not self.send_get_peers():
            utils.printer.printout("Couldn't send the get peers message!")
            return False
        return True

    def gossip_object(self, ob_hash) -> int:
        obj_message = {
                "type": "ihaveobject",
                "objectid": ob_hash
        }

        msg = json.dumps(obj_message) + "\n"
        message = msg.encode(self.FORMAT)
        utils.printer.printout("[SENT] " + msg)

        # FIX: broadcast to all, might need to loop through all clients
        return self.conn.sendto(message, ('<broadcast>', self.addr[1]))

    def send_object(self, msg) -> bool:
        """Triggered by 'getobject'. Send back the requested object if we have it in db"""

        if not self.check_msg_format(msg, 2, ["objectid"], "getobject has wrong format"):
            return False

        ob_hash = msg["objectid"]
        if utils.object_saver.objects.__contains__(ob_hash):
            obj = utils.object_saver.objects.get(ob_hash)
            return self.send_message({
                "type": "object",
                "object": {
                    "type": obj.type,
                    "txids": obj.txids,
                    "nonce": obj.nonce,
                    "previd": obj.previd,
                    "created": obj.created,
                    "T": obj.T
                }
            })

        return True

    def process_i_have_object(self, msg) -> bool:
        """Triggered by 'ihaveobject'. Check if we already have this object and if not, request it"""

        if not self.check_msg_format(msg, 2, ["objectid"], "ihaveobject has wrong format"):
            return False

        ob_hash = msg["objectid"]
        if not utils.object_saver.objects.__contains__(ob_hash):
            return self.send_message({
                "type": "getobject",
                "objectid": ob_hash
            })

        return True

    def receive_object(self, msg) -> bool:
        """Triggered by 'object'.
            - Receive and store a new object, if it isn't already present in our db.
            - Gossip it to other peers"""

        if not self.check_msg_format(msg, 2, ["object"], "message of type 'object' has wrong format"):
            return False

        # Generate a TxObject instance
        ob = msg["object"]
        if "type" not in ob.keys():
            return False

        # For block objects
        if ob["type"] == "block":
            if self.check_msg_format(ob, 6, ["type", "txids", "nonce", "previd", "created", "T"], "message of type 'object' has wrong format"):
                ob_obj = TxObject(ob["type"], ob["txids"], ob["nonce"], ob["previd"], ob["created"], ob["T"])

                # Generate the hash value
                ob_hash = sha256(str(ob_obj).encode('utf-8')).hexdigest()

                utils.printer.printout("Received object with hash " + ob_hash)

                # Store Object in DB, if we don't already have it
                if not utils.object_saver.objects.__contains__(ob_hash):
                    obj_mapping = [(ob_hash, ob_obj)]
                    utils.object_saver.add_object(obj_mapping)
                    # TODO: Gossip it
                    
                    threading.Thread(target=self.object_got, args=(ob_hash))
        
        # For transaction objects
        elif ob["type"] == "transaction":
            if "height" in ob.keys():
                ob_obj = CoinbaseTransaction(ob["type"], ob["height"], ob["outputs"])
                # What do we want as the key for a coinbase transaction?
                obj_mapping = [(str(ob["height"]) + ob["outputs"][0]["pubkey"], ob_obj)]
                utils.object_saver.add_object(obj_mapping)

            elif self.valid_transaction(ob):
                ob_obj = TransactionObject(ob["type"], ob["inputs"], ob["outputs"])
                obj_mapping = [(ob["inputs"][0]["outpoint"]["txid"], ob_obj)]
                utils.object_saver.add_object(obj_mapping)

        return True

    async def maintain_connection(self) -> None:
        """Loop trough new messages and answer them"""

        hello_received = False
        valid_types = ["hello", "getpeers", "peers", "getobject", "ihaveobject", "object"]

        # Loop trough new received messages
        while True:
            msgs = await self.receive_msg()

            # received something bad
            if msgs is None:
                if not hello_received:  # only close connection, if invalid input was received before hello message
                    utils.printer.printout("Connection got closed, exiting!")
                    return
                else:  # if invalid input was received after hello, we already sent an error message and now just discard the message
                    continue

            if msgs is "kill":  # connection got killed
                utils.printer.printout("Connection got closed, exiting!")
                return

            for msg in msgs:
                print(msg)
                if "type" not in msg:
                    self.send_error("No valid message received")

                if msg["type"] == "hello":
                    hello_received = self.receive_hello(msg)

                if not hello_received:
                    self.send_error("Sent no hello message at start of conversation.")
                    return

                if msg["type"] == "getpeers":
                    if not self.send_peers(msg):
                        return

                if msg["type"] == "peers":
                    if not self.receive_peers(msg):
                        return

                if msg["type"] == "getobject":
                    if not self.send_object(msg):
                        return

                if msg["type"] == "object":
                    if not self.receive_object(msg):
                        return

                if msg["type"] == "ihaveobject":
                    if not self.process_i_have_object(msg):
                        return

                if msg["type"] not in valid_types:
                    # We should handle this somehow
                    utils.printer.printout("Unknown type: " + msg["type"])
                    continue
