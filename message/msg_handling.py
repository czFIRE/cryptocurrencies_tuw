import asyncio
import json
import ipaddress
import threading
import message.msg_builder as build
import logging as log
import constants as const

from asyncio import StreamWriter
from message.msg_builder import serialize_msg
from objects.Block import Block
from objects.UtxoSet import UtxoSet
from objects.Transaction import Transaction
from peers.Peer import Peer
from objects.obj_validation import validate_object
from global_variables import DB_MANAGER, CONNECTIONS
from message.msg_exceptions import UnexpectedMsgException, ErrorMsgException
from objects.obj_exceptions import ValidationException

async def write_msg(writer: StreamWriter, msg_dict: json):
    msg_str = serialize_msg(msg_dict)
    writer.write(msg_str.encode("utf-8"))
    await writer.drain()


def handle_hello_msg():
    raise UnexpectedMsgException("Additional 'Hello' message while already connected")


async def handle_getpeers_msg(writer: StreamWriter, peer: Peer):
    peers = DB_MANAGER.get_peers()
    peers_msg = build.peers_msg(peers)

    log.debug(f"Sending peers message to {peer} ({len(peers)} peers)")
    await write_msg(writer, peers_msg)
    log.info(f"'Peers' message send to {peer}")


def handle_peers_msg(msg_dict: json):
    peers = []
    for p in msg_dict['peers']:
        host, port = p.split(':')
        host = host.strip('[]')

        # Sanitize IP Addresses
        if host in const.BANNED_HOSTS:
            continue
        try:
            ip = ipaddress.ip_address(host)
            # We need to do this because other students add literally everything to their databases which
            # causes us headaches...
            if not ip.is_global or ip.is_multicast:
                continue
        except ValueError as e:
            log.info(f"IP address {host} is invalid.")
            continue

        peers.append(Peer(host, int(port)))

    DB_MANAGER.add_peers(peers)


def handle_error_msg():
    raise ErrorMsgException()


async def handle_object_msg(msg_dict: json, peer: Peer):
    obj_dict = msg_dict["object"]

    match obj_dict["type"]:
        case "transaction":
            log.debug(f"Handle Transaction message")
            obj = Transaction.load_from_json(obj_dict)
        case "block":
            log.debug(f"Handle Block message")
            obj = Block.load_from_json(obj_dict)
        case _:
            raise ValueError("Unexpected object type")

    if not await validate_object(obj, peer):
        raise ValidationException()

    if isinstance(obj, Block):
        if not update_utxo_set(obj):
            return

    if DB_MANAGER.add_object(obj):
        log.info(f"Stored new object with ID {obj.object_id} in DB")
        log.info(f"Gossip object with ID {obj.object_id} to the following peers: {list(CONNECTIONS.keys())}")
        # Gossiping
        for writer in CONNECTIONS.values():
            await write_msg(writer, build.ihaveobject_msg(obj.object_id))


def update_utxo_set(block: Block) -> bool:
    log.debug(f"Calculating new UTXO set for block {block}")
    state = {}

    if block.previd is not None:
        log.debug(f"Load state for block {block.object_id}")
        prev_utxo = UtxoSet.load_from_json(json.loads(DB_MANAGER.get_utxo_set(block.previd)))
        log.debug(f"Loaded utxo for block {block.object_id}: {prev_utxo}")
        if prev_utxo.state is not None:
            state = prev_utxo.state
        log.debug(f"Loaded state of block {block.object_id}: {state}")

    for tx_id in block.txids:
        transaction = Transaction.load_from_json(json.loads(DB_MANAGER.get_tx_obj(tx_id)))
        if transaction.inputs is not None:
            for tx_input in transaction.inputs:
                input_tx_id = tx_input["outpoint"]["txid"]
                input_tx_index = tx_input["outpoint"]["index"]
                if state.get(input_tx_id)[input_tx_index] is None or \
                        state.get(input_tx_id)[input_tx_index][
                            "value"] == 0:  # Referenced transaction does not exist in state
                    
                    return False # TODO - what the heck does this do? 

                state.get(input_tx_id)[input_tx_index]["value"] = 0  # Mark output as spent

        state[tx_id] = transaction.outputs  # Add the outputs of the new transaction to the state

    new_set = UtxoSet(block.object_id, state)

    log.debug(f"Adding new UTXO set {new_set.set_id} with state {new_set.state} to DB")

    return DB_MANAGER.add_utxo_set(new_set)


async def handle_ihaveobject_msg(writer: StreamWriter, msg_dict: json, peer: Peer):
    if not DB_MANAGER.get_object(msg_dict["objectid"]):
        log.debug(f"Promoted object from peer {peer} is not in the DB")
        await write_msg(writer, build.getobject_msg(msg_dict["objectid"]))
        log.info(f"'GetObject' message send to {peer}")


async def handle_getobject_msg(writer: StreamWriter, msg_dict: json, peer: Peer):
    obj = DB_MANAGER.get_object(msg_dict["objectid"])
    if obj:
        log.debug(f"Object requested by peer {peer} was found in the DB")
        await write_msg(writer, build.object_msg(obj))
        log.info(f"'Object' message send to {peer}")
    else:
        log.debug(f"Object requested by peer {peer} is not in the DB")


async def handle_msg(writer: StreamWriter, msg_type: str, msg: json, peer: Peer):
    log.info(f"Handle message from peer {peer} with type {msg_type}")
    match msg_type:
        case 'hello':
            handle_hello_msg()
        case 'getpeers':
            await handle_getpeers_msg(writer, peer)
        case 'peers':
            handle_peers_msg(msg)
        case 'error':
            handle_error_msg()
        case 'object':
            # await handle_object_msg(msg, peer)
            task = threading.Thread(target=asyncio.run, args=(handle_object_msg(msg, peer),))
            task.start()
        case 'ihaveobject':
            await handle_ihaveobject_msg(writer, msg, peer)
        case 'getobject':
            await handle_getobject_msg(writer, msg, peer)
