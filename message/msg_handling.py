import asyncio
import json
import ipaddress
import message.msg_builder as build
import logging as log
import constants as const

from asyncio import StreamWriter
from message.msg_builder import serialize_msg
from objects.Block import Block
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
            obj = Transaction.load_from_json(obj_dict)
        case "block":
            obj = Block.load_from_json(obj_dict)
        case _:
            raise ValueError("Unexpected object type")

    if not await validate_object(obj, peer):
        raise ValidationException()

    if DB_MANAGER.add_object(obj):
        log.info(f"Stored new object with ID {obj.object_id} in DB")
        log.info(f"Gossip object with ID {obj.object_id} to the following peers: {list(CONNECTIONS.keys())}")
        # Gossiping
        for writer in CONNECTIONS.values():
            await write_msg(writer, build.ihaveobject_msg(obj.object_id))

        if isinstance(obj, Block):
            # TODO update UTXO 
            pass


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
            await handle_object_msg(msg, peer)
        case 'ihaveobject':
            await handle_ihaveobject_msg(writer, msg, peer)
        case 'getobject':
            await handle_getobject_msg(writer, msg, peer)
